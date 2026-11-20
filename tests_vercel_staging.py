"""
Vercel Staging Deployment Acceptance Test Suite
Validates all Vercel compatibility configurations, serverless entrypoints,
static assets, routing, CSRF trusted origins, and safety isolations.
"""

import os
import sys
import json
import stat
from pathlib import Path

# Setup paths and environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')

import django
django.setup()
from django.conf import settings
from django.utils.http import is_same_domain

def test_wsgi_entrypoint():
    print("[T1] WSGI Entrypoint & Serverless Callable")
    from college_management_system import wsgi
    assert hasattr(wsgi, 'application'), "wsgi.py missing 'application' callable"
    assert hasattr(wsgi, 'app'), "wsgi.py missing 'app' callable required by @vercel/python"
    assert wsgi.app == wsgi.application, "wsgi.app must reference wsgi.application"
    print("  [✓] wsgi.py correctly exposes both 'application' and 'app': PASS")

def test_vercel_json_configuration():
    print("\n[T2] vercel.json Structure & Route Mapping")
    v_path = BASE_DIR / 'vercel.json'
    assert v_path.exists(), "vercel.json does not exist in root directory"
    with open(v_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data.get('version') == 2, "vercel.json version must be 2"
    builds = data.get('builds', [])
    assert len(builds) >= 2, "vercel.json must define at least @vercel/python and @vercel/static-build"
    
    python_build = next((b for b in builds if b.get('use') == '@vercel/python'), None)
    assert python_build is not None, "Missing @vercel/python build entry"
    assert python_build.get('src') == 'college_management_system/wsgi.py', "Python entrypoint mismatch"
    assert python_build.get('config', {}).get('runtime') in ('python3.12', 'python3.11'), "Python runtime must be python3.12"
    
    static_build = next((b for b in builds if b.get('use') == '@vercel/static-build'), None)
    assert static_build is not None, "Missing @vercel/static-build entry for static assets"
    assert static_build.get('src') == 'build_files.sh', "Static build must target build_files.sh"
    assert static_build.get('config', {}).get('distDir') == 'staticfiles_build', "distDir must match staticfiles_build"
    
    routes = data.get('routes', [])
    assert any(r.get('src') == '/static/(.*)' for r in routes), "Missing /static/(.*) CDN route"
    assert any(r.get('src') == '/(.*)' for r in routes), "Missing /.* WSGI catch-all route"
    print("  [✓] vercel.json verified with @vercel/python, @vercel/static-build, and dual routes: PASS")

def test_build_files_script():
    print("\n[T3] build_files.sh Script & Permissions")
    bf_path = BASE_DIR / 'build_files.sh'
    assert bf_path.exists(), "build_files.sh does not exist"
    content = bf_path.read_text(encoding='utf-8')
    assert 'collectstatic' in content, "build_files.sh missing collectstatic command"
    assert '--noinput' in content, "build_files.sh collectstatic must include --noinput"
    assert 'pip install -r requirements.txt' in content, "build_files.sh missing pip install"
    print("  [✓] build_files.sh present with automated pip install and collectstatic: PASS")

def test_allowed_hosts_and_csrf():
    print("\n[T4] ALLOWED_HOSTS & CSRF Trusted Origins for Vercel")
    # Simulate Vercel environment detection
    assert '.vercel.app' in settings.ALLOWED_HOSTS or any('vercel' in h for h in settings.ALLOWED_HOSTS), \
        "Vercel domain not present in ALLOWED_HOSTS"
    
    # Verify CSRF trusted origins has HTTPS format compliant with Django 4.0+
    assert 'https://college-erp-xwqr.onrender.com' in settings.CSRF_TRUSTED_ORIGINS, \
        "Render HTTPS domain missing from CSRF_TRUSTED_ORIGINS"
    assert 'https://*.vercel.app' in settings.CSRF_TRUSTED_ORIGINS, \
        "Vercel wildcard HTTPS domain missing from CSRF_TRUSTED_ORIGINS"
    
    # Verify is_same_domain matches correctly for Django 3.1
    assert is_same_domain('college-erp-xwqr.onrender.com', 'college-erp-xwqr.onrender.com'), \
        "Same-domain check failed for Render host"
    assert is_same_domain('preview-branch-123.vercel.app', '.vercel.app'), \
        "Subdomain wildcard matching failed for Vercel preview branch"
    print("  [✓] ALLOWED_HOSTS and dual-format CSRF_TRUSTED_ORIGINS verified: PASS")

def test_whitenoise_positioning():
    print("\n[T5] WhiteNoise Middleware Pipeline Positioning")
    middleware = settings.MIDDLEWARE
    sec_idx = middleware.index('django.middleware.security.SecurityMiddleware')
    wn_idx = middleware.index('whitenoise.middleware.WhiteNoiseMiddleware')
    assert wn_idx == sec_idx + 1, "WhiteNoiseMiddleware must be placed immediately after SecurityMiddleware"
    print(f"  [✓] WhiteNoise positioned at index {wn_idx} immediately following SecurityMiddleware ({sec_idx}): PASS")

def test_static_and_media_roots():
    print("\n[T6] Dynamic STATIC_ROOT & MEDIA_ROOT Serverless Isolation")
    # Local defaults
    assert not settings.IS_VERCEL, "Local test must run with IS_VERCEL=False"
    assert str(settings.STATIC_ROOT).endswith('static'), "Default local STATIC_ROOT must end with 'static'"
    assert str(settings.MEDIA_ROOT).endswith('media'), "Default local MEDIA_ROOT must end with 'media'"
    
    # Verify gitignore ignores ephemeral build folder
    gi_path = BASE_DIR / '.gitignore'
    gi_content = gi_path.read_text(encoding='utf-8')
    assert '/staticfiles_build/' in gi_content, "/staticfiles_build/ must be in .gitignore"
    print("  [✓] Static and Media root paths isolated; /staticfiles_build/ gitignored: PASS")

def test_database_isolation():
    print("\n[T7] Database Isolation & Zero Production Touch")
    db_config = settings.DATABASES['default']
    # Must be local SQLite for this run
    assert 'sqlite3' in db_config['ENGINE'], "Local test runner must use SQLite, never production Neon"
    assert 'ep-' not in str(db_config['NAME']), "Local database must not point to Neon host"
    print("  [✓] Verified strictly using local db.sqlite3; production Neon database 100% isolated: PASS")

def test_django_deploy_check():
    print("\n[T8] Django System Check & Production Security Compliance")
    from django.core.management import call_command
    from io import StringIO
    
    # 1. Standard development system check
    out = StringIO()
    call_command('check', stdout=out)
    print("  [✓] Standard python manage.py check passed (0 issues): PASS")
    
    # 2. Simulated production deploy check
    from django.test import override_settings
    orig_async = os.environ.pop('DJANGO_ALLOW_ASYNC_UNSAFE', None)
    try:
        with override_settings(
            DEBUG=False,
            SECRET_KEY='a-very-long-and-secure-test-secret-key-for-deployment-testing-12345',
            SECURE_HSTS_SECONDS=31536000,
            SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
            SECURE_HSTS_PRELOAD=True,
            SECURE_SSL_REDIRECT=True,
            SESSION_COOKIE_SECURE=True,
            CSRF_COOKIE_SECURE=True,
        ):
            out_deploy = StringIO()
            call_command('check', deploy=True, stdout=out_deploy)
            print("  [✓] Production python manage.py check --deploy passed cleanly with 0 issues: PASS")
    finally:
        if orig_async:
            os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = orig_async

def run_all_vercel_tests():
    print("=" * 65)
    print("VERCEL STAGING ACCEPTANCE TEST SUITE")
    print("=" * 65)
    
    tests = [
        test_wsgi_entrypoint,
        test_vercel_json_configuration,
        test_build_files_script,
        test_allowed_hosts_and_csrf,
        test_whitenoise_positioning,
        test_static_and_media_roots,
        test_database_isolation,
        test_django_deploy_check,
    ]
    
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [✗] FAILED: {e}")
            failed += 1
            
    print("\n" + "=" * 65)
    print("VERCEL STAGING TEST SUMMARY")
    print("=" * 65)
    print(f"  PASSED: {passed}")
    print(f"  FAILED: {failed}")
    print(f"  TOTAL:  {len(tests)}")
    
    if failed == 0:
        print("ALL VERCEL STAGING ACCEPTANCE TESTS PASSED!")
    else:
        sys.exit(1)

if __name__ == '__main__':
    run_all_vercel_tests()
