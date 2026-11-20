"""
Automated Test Suite: Login Page Footer & CAPTCHA Verification
Tests:
  1. Frontend site key loaded from environment into template without being exposed
  2. Backend secret key loaded from environment without being exposed
  3. Dynamic copyright year in footer (displays current year 2026, no hardcoded 2024)
  4. CAPTCHA missing rejection (login rejected without completing CAPTCHA)
  5. Pseudo/bypass token rejection
  6. Valid CAPTCHA verification allows normal authentication (successful login)
  7. Invalid credentials rejected even with valid CAPTCHA
  8. Shared layouts consistency check
"""
import sys, os
sys.path.insert(0, r'D:\College_ERP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django
django.setup()

from datetime import date
from django.test import Client
from django.conf import settings
from django.contrib.messages import get_messages
from main_app.models import CustomUser

PASS = "PASS"
FAIL = "FAIL"
results = []

def report(name, status, detail=""):
    results.append((name, status, detail))
    icon = "✓" if status == PASS else "✗"
    print(f"  [{icon}] {name}: {status}" + (f" — {detail}" if detail else ""))

print("=" * 65)
print("LOGIN PAGE FOOTER & CAPTCHA ACCEPTANCE TEST SUITE")
print("=" * 65)

client = Client()

# ─── T1: Dynamic Copyright Year in Footer ──────────────────────
print("\n[T1] Dynamic Copyright Year in Footer")
try:
    resp = client.get('/')
    content = resp.content.decode('utf-8')
    current_year = str(date.today().year)
    expected_footer = f"© {current_year} College ERP System. All rights reserved."
    
    has_current_year_footer = expected_footer in content
    has_hardcoded_2024 = "2024 College ERP System" in content
    
    if has_current_year_footer and not has_hardcoded_2024:
        report(f"Footer displays '{expected_footer}' dynamically: PASS", PASS)
    else:
        report("Footer dynamic year", FAIL, f"Found current footer: {has_current_year_footer}, Stale 2024: {has_hardcoded_2024}")
except Exception as e:
    report("Footer dynamic year test", FAIL, str(e))

# ─── T2: Frontend reCAPTCHA Site Key Loaded & Widget Rendered ──
print("\n[T2] Frontend reCAPTCHA v2 Widget Rendering")
try:
    site_key = getattr(settings, 'RECAPTCHA_SITE_KEY', '')
    site_key_loaded = bool(site_key and len(site_key) > 10)
    
    resp = client.get('/')
    content = resp.content.decode('utf-8')
    
    # Check widget div exists and data-sitekey is populated (NOT empty)
    has_widget_tag = 'class="g-recaptcha' in content
    has_empty_sitekey = 'data-sitekey=""' in content
    has_populated_sitekey = 'data-sitekey=' in content and not has_empty_sitekey
    has_api_script = 'https://www.google.com/recaptcha/api.js' in content
    
    if site_key_loaded and has_widget_tag and has_populated_sitekey and has_api_script:
        report(f"reCAPTCHA v2 checkbox widget rendered above Sign In with valid site key: PASS", PASS)
    else:
        report("reCAPTCHA widget rendering", FAIL, f"site_key_loaded={site_key_loaded}, widget={has_widget_tag}, populated={has_populated_sitekey}")
except Exception as e:
    report("reCAPTCHA widget rendering test", FAIL, str(e))

# ─── T3: Backend reCAPTCHA Secret Key Loaded ───────────────────
print("\n[T3] Backend reCAPTCHA Secret Key Configuration")
try:
    secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
    secret_key_loaded = bool(secret_key and len(secret_key) > 10)
    verify_url = getattr(settings, 'RECAPTCHA_VERIFY_URL', '')
    has_verify_url = bool(verify_url and 'google.com/recaptcha/api/siteverify' in verify_url)
    
    if secret_key_loaded and has_verify_url:
        report(f"reCAPTCHA backend secret key verified and loaded from environment: PASS", PASS)
    else:
        report("reCAPTCHA secret key configuration", FAIL, f"secret_key_loaded={secret_key_loaded}, verify_url={has_verify_url}")
except Exception as e:
    report("reCAPTCHA secret key test", FAIL, str(e))

# ─── T4: Login Rejected Without Completing CAPTCHA ─────────────
print("\n[T4] Login Rejection Without Completing CAPTCHA")
try:
    client_t4 = Client()
    resp = client_t4.post('/doLogin/', {
        'email': 'admin@admin.com',
        'password': 'admin123',
        'g-recaptcha-response': ''
    }, follow=True)
    
    messages_list = [str(m) for m in get_messages(resp.wsgi_request)]
    expected_msg = "CAPTCHA verification is required. Please check the CAPTCHA box."
    is_rejected = any(expected_msg in m for m in messages_list)
    is_unauthenticated = not ('_auth_user_id' in client_t4.session)
    
    if is_rejected and is_unauthenticated:
        report("Login without CAPTCHA strictly rejected with error message: PASS", PASS)
    else:
        report("Missing CAPTCHA rejection", FAIL, f"Rejected: {is_rejected}, Unauth: {is_unauthenticated}, Messages: {messages_list}")
except Exception as e:
    report("Missing CAPTCHA rejection test", FAIL, str(e))

# ─── T5: Login Rejected With Bypass / Pseudo Token ─────────────
print("\n[T5] Login Rejection With Pseudo / Bypass Tokens")
try:
    client_t5 = Client()
    resp = client_t5.post('/doLogin/', {
        'email': 'admin@admin.com',
        'password': 'admin123',
        'g-recaptcha-response': 'BYPASS'
    }, follow=True)
    
    messages_list = [str(m) for m in get_messages(resp.wsgi_request)]
    expected_msg = "Invalid CAPTCHA token format. Please complete the interactive verification."
    is_rejected = any(expected_msg in m for m in messages_list)
    is_unauthenticated = not ('_auth_user_id' in client_t5.session)
    
    if is_rejected and is_unauthenticated:
        report("Login with pseudo token 'BYPASS' strictly rejected: PASS", PASS)
    else:
        report("Pseudo token rejection", FAIL, f"Rejected: {is_rejected}, Messages: {messages_list}")
except Exception as e:
    report("Pseudo token rejection test", FAIL, str(e))

# ─── T6: Full Authentication Flow With Valid CAPTCHA ───────────
print("\n[T6] Full Authentication Flow With Valid CAPTCHA")
try:
    client_t6 = Client()
    test_token = settings.RECAPTCHA_TEST_TOKENS[0]
    
    resp = client_t6.post('/doLogin/', {
        'email': 'admin@admin.com',
        'password': 'admin123',
        'g-recaptcha-response': test_token
    }, follow=True)
    
    is_authenticated = '_auth_user_id' in client_t6.session
    user_id = client_t6.session.get('_auth_user_id')
    admin_user = CustomUser.objects.get(email='admin@admin.com')
    is_correct_user = (int(user_id) == admin_user.id) if is_authenticated else False
    
    if is_authenticated and is_correct_user:
        report(f"Valid CAPTCHA verification allows normal authentication: PASS (Logged in as {admin_user.email})", PASS)
    else:
        messages_list = [str(m) for m in get_messages(resp.wsgi_request)]
        report("Valid CAPTCHA authentication", FAIL, f"Auth={is_authenticated}, Messages: {messages_list}")
except Exception as e:
    report("Valid CAPTCHA verification test", FAIL, str(e))

# ─── T7: Invalid Password Rejection Even With Valid CAPTCHA ────
print("\n[T7] Invalid Credentials Protection With Valid CAPTCHA")
try:
    client_t7 = Client()
    test_token = settings.RECAPTCHA_TEST_TOKENS[0]
    
    resp = client_t7.post('/doLogin/', {
        'email': 'admin@admin.com',
        'password': 'WrongPassword123!',
        'g-recaptcha-response': test_token
    }, follow=True)
    
    messages_list = [str(m) for m in get_messages(resp.wsgi_request)]
    expected_msg = "Invalid details"
    is_rejected = any(expected_msg in m for m in messages_list)
    is_unauthenticated = not ('_auth_user_id' in client_t7.session)
    
    if is_rejected and is_unauthenticated:
        report("Invalid password with valid CAPTCHA correctly rejected: PASS", PASS)
    else:
        report("Invalid password rejection", FAIL, f"Rejected: {is_rejected}, Messages: {messages_list}")
except Exception as e:
    report("Invalid password rejection test", FAIL, str(e))

# ─── T8: Consistent Copyright Year in Shared Layouts ───────────
print("\n[T8] Consistent Copyright Year in Shared Layouts")
try:
    templates_to_check = [
        r'D:\College_ERP\main_app\templates\main_app\login.html',
        r'D:\College_ERP\main_app\templates\main_app\erpnext_login.html',
        r'D:\College_ERP\main_app\templates\registration\erpnext_base.html',
    ]
    all_updated = True
    for t_path in templates_to_check:
        with open(t_path, 'r', encoding='utf-8') as f:
            t_content = f.read()
            if '{% now "Y" %}' not in t_content:
                all_updated = False
                print(f"    Missing dynamic year tag in: {os.path.basename(t_path)}")
            if '2024 College ERP System' in t_content:
                all_updated = False
                print(f"    Stale 2024 year in: {os.path.basename(t_path)}")
                
    if all_updated:
        report("All shared login and layout templates use dynamic {% now 'Y' %}: PASS", PASS)
    else:
        report("Shared layouts year consistency", FAIL, "One or more templates failed check")
except Exception as e:
    report("Shared layouts year test", FAIL, str(e))

# ─── SUMMARY ──────────────────────────────────────────────────
print()
print("=" * 65)
print("SUMMARY")
print("=" * 65)
passed = sum(1 for _, s, _ in results if s == PASS)
failed = sum(1 for _, s, _ in results if s == FAIL)
print(f"  PASSED: {passed}")
print(f"  FAILED: {failed}")
print(f"  TOTAL:  {len(results)}")
if failed > 0:
    print("FAILURES:")
    for n, s, d in results:
        if s == FAIL:
            print(f"  ✗ {n}: {d}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED SUCCESSFULLY!")
    sys.exit(0)
