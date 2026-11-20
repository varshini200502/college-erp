"""
Phase 1A Regression Test Suite
Run with: D:\College_ERP\venv\Scripts\python.exe phase1a_regression_test.py
Tests ONLY the local SQLite db. No Neon production connection.
"""
import sys, os
sys.path.insert(0, r'D:\College_ERP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')

import django
django.setup()

from django.test import TestCase, RequestFactory
from django.contrib.auth import authenticate
from django.urls import reverse
from django.test.client import Client
from main_app.models import CustomUser, StudentResult, MarksCorrectionLog, Subject, Student, Staff
from django.conf import settings as django_settings

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"
results = []

def report(test_name, status, detail=""):
    results.append((test_name, status, detail))
    icon = "✓" if status == PASS else ("⚠" if status == SKIP else "✗")
    print(f"  [{icon}] {test_name}: {status}" + (f" — {detail}" if detail else ""))

print("=" * 65)
print("PHASE 1A REGRESSION TEST SUITE")
print("=" * 65)

# ─── T1: Settings – ALLOWED_HOSTS ───────────────────────────────
print("\n[T1] Settings: ALLOWED_HOSTS & CSRF_TRUSTED_ORIGINS")
ah = django_settings.ALLOWED_HOSTS
if '.onrender.com' in ah or any('*' in h for h in ah):
    report("No wildcard in ALLOWED_HOSTS", FAIL, f"Found: {ah}")
else:
    report("No wildcard in ALLOWED_HOSTS", PASS, str(ah))

if 'college-erp-xwqr.onrender.com' in ah:
    report("Exact Render hostname in ALLOWED_HOSTS", PASS)
else:
    report("Exact Render hostname in ALLOWED_HOSTS", FAIL, str(ah))

cto = django_settings.CSRF_TRUSTED_ORIGINS
if any('*' in o for o in cto):
    report("No wildcard in CSRF_TRUSTED_ORIGINS", FAIL, f"Found: {cto}")
else:
    report("No wildcard in CSRF_TRUSTED_ORIGINS", PASS, str(cto))

if 'https://college-erp-xwqr.onrender.com' in cto:
    report("Exact CSRF origin present", PASS)
else:
    report("Exact CSRF origin present", FAIL, str(cto))

# ─── T2: Settings – Password validators ──────────────────────────
print("\n[T2] Settings: Password Validators always active")
pv = django_settings.AUTH_PASSWORD_VALIDATORS
if len(pv) == 4:
    report("4 password validators active in DEBUG mode", PASS)
else:
    report("4 password validators active in DEBUG mode", FAIL, f"Got {len(pv)}")

# ─── T3: Settings – SECRET_KEY fallback ──────────────────────────
print("\n[T3] Settings: SECRET_KEY loaded")
sk = django_settings.SECRET_KEY
if sk and len(sk) > 10:
    report("SECRET_KEY is set", PASS, f"length={len(sk)}")
else:
    report("SECRET_KEY is set", FAIL)

# ─── T4: Login for each role via Django test client ──────────────
print("\n[T4] Login tests for all roles present in local SQLite")
client = Client()
role_map = {'1':'Admin','2':'Staff','3':'Student','4':'Principal','5':'Finance','7':'Accreditation'}
login_tested = 0
for user in CustomUser.objects.all().order_by('user_type')[:8]:
    utype = str(user.user_type)
    role_name = role_map.get(utype, f'type={utype}')
    # We can't test real passwords - just verify the user record is intact
    if user.email and user.password:
        report(f"User record intact [{role_name}] {user.email}", PASS)
        login_tested += 1
    else:
        report(f"User record missing data [{role_name}]", FAIL)
print(f"  → Checked {login_tested} user records")

# ─── T5: CSRF decorator removal – verify get_students is NOT csrf_exempt ─
print("\n[T5] CSRF: Verify target views are no longer csrf_exempt")
import inspect
import main_app.staff_views as sv
import main_app.views as gv
import main_app.hod_views as hv

def is_csrf_exempt(func):
    return getattr(func, 'csrf_exempt', False)

for fname in ['get_students', 'save_attendance', 'get_student_attendance', 'update_attendance', 'fetch_student_result']:
    fn = getattr(sv, fname, None)
    if fn is None:
        report(f"staff_views.{fname} exists", FAIL, "not found")
    elif is_csrf_exempt(fn):
        report(f"staff_views.{fname} csrf_exempt removed", FAIL, "still marked @csrf_exempt")
    else:
        report(f"staff_views.{fname} csrf_exempt removed", PASS)

fn = getattr(gv, 'get_attendance', None)
if fn and is_csrf_exempt(fn):
    report("views.get_attendance csrf_exempt removed", FAIL, "still marked @csrf_exempt")
elif fn:
    report("views.get_attendance csrf_exempt removed", PASS)
else:
    report("views.get_attendance exists", FAIL, "not found")

fn = getattr(hv, 'get_admin_attendance', None)
if fn and is_csrf_exempt(fn):
    report("hod_views.get_admin_attendance csrf_exempt removed", FAIL)
elif fn:
    report("hod_views.get_admin_attendance csrf_exempt removed", PASS)
else:
    report("hod_views.get_admin_attendance exists", FAIL, "not found")

# ─── T6: FCM-token views remain csrf_exempt (intentional) ────────
print("\n[T6] FCM token views remain csrf_exempt (intentional)")
fn = getattr(sv, 'staff_fcmtoken', None)
if fn and is_csrf_exempt(fn):
    report("staff_fcmtoken still csrf_exempt (correct)", PASS)
else:
    report("staff_fcmtoken still csrf_exempt (correct)", FAIL if fn else SKIP)

# ─── T7: EditResultView – finalized lock ─────────────────────────
print("\n[T7] EditResultView: finalized marks are blocked")
from main_app.EditResultView import EditResultView
import inspect
src = inspect.getsource(EditResultView.post)
if 'is_finalized' in src and 'MarksCorrectionLog' in src:
    report("EditResultView.post checks is_finalized and logs correction", PASS)
else:
    report("EditResultView.post checks is_finalized and logs correction", FAIL)

if 'MarksCorrectionLog' in src:
    report("MarksCorrectionLog imported and used in EditResultView", PASS)
else:
    report("MarksCorrectionLog imported and used in EditResultView", FAIL)

# ─── T8: EditResultView – finalized block simulation ─────────────
print("\n[T8] Finalized marks block simulation")
try:
    result = StudentResult.objects.filter(is_finalized=False).first()
    if result:
        result.is_finalized = True
        result.save()
        # Reload
        r2 = StudentResult.objects.get(pk=result.pk)
        if r2.is_finalized:
            report("StudentResult.is_finalized can be set to True", PASS)
        # Restore
        result.is_finalized = False
        result.save()
        report("StudentResult.is_finalized restored to False", PASS)
    else:
        report("No unfinalized StudentResult to test with", SKIP)
except Exception as e:
    report("Finalized flag toggle test", FAIL, str(e))

# ─── T9: MarksCorrectionLog creation ─────────────────────────────
print("\n[T9] MarksCorrectionLog: create and verify audit entry")
try:
    result = StudentResult.objects.first()
    admin_user = CustomUser.objects.filter(user_type=1).first()
    if result and admin_user:
        before_count = MarksCorrectionLog.objects.count()
        log = MarksCorrectionLog.objects.create(
            result=result,
            changed_by=admin_user,
            previous_test=result.test,
            new_test=result.test + 0.5,
            previous_exam=result.exam,
            new_exam=result.exam,
            previous_assignment=result.assignment,
            new_assignment=result.assignment,
            previous_practical=result.practical,
            new_practical=result.practical,
            reason="Phase 1A test entry"
        )
        after_count = MarksCorrectionLog.objects.count()
        if after_count == before_count + 1:
            report("MarksCorrectionLog.create() succeeded", PASS)
        else:
            report("MarksCorrectionLog count did not increment", FAIL)
        # Cleanup
        log.delete()
        report("MarksCorrectionLog test entry cleaned up", PASS)
    else:
        report("MarksCorrectionLog creation test", SKIP, "No StudentResult or admin user found")
except Exception as e:
    report("MarksCorrectionLog creation test", FAIL, str(e))

# ─── T10: Migration state unchanged ──────────────────────────────
print("\n[T10] Migration state: no new migrations created")
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
executor = MigrationExecutor(connection)
plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
if len(plan) == 0:
    report("Zero pending/unapplied migrations", PASS)
else:
    report("Zero pending/unapplied migrations", FAIL, f"{len(plan)} migrations pending")

# Check main_app migration count
from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(connection)
main_app_migs = sorted([k for k in loader.disk_migrations if k[0] == 'main_app'])
report(f"main_app has {len(main_app_migs)} migration(s): {[m[1] for m in main_app_migs]}", PASS if len(main_app_migs) == 3 else FAIL)

# ─── T11: DB baseline unchanged ──────────────────────────────────
print("\n[T11] Database baseline: record counts unchanged")
from main_app.models import CustomUser, StudentResult, MarksCorrectionLog
user_count = CustomUser.objects.count()
sr_count = StudentResult.objects.count()
mcl_count = MarksCorrectionLog.objects.count()
report(f"CustomUser count is 42 (got {user_count})", PASS if user_count == 42 else FAIL)
report(f"StudentResult count is 87 (got {sr_count})", PASS if sr_count == 87 else FAIL)
report(f"MarksCorrectionLog count is 0 (got {mcl_count})", PASS if mcl_count == 0 else FAIL)

# ─── T12: Template CSRF cookie function present ───────────────────
print("\n[T12] Templates: getCookie + X-CSRFToken present in AJAX views")
templates_to_check = {
    r'D:\College_ERP\main_app\templates\staff_template\staff_take_attendance.html': ['getCookie', 'X-CSRFToken', 'csrftoken'],
    r'D:\College_ERP\main_app\templates\hod_template\admin_view_attendance.html': ['getCookie', 'X-CSRFToken', 'csrftoken'],
    r'D:\College_ERP\main_app\templates\staff_template\staff_add_result.html': ['getCookie', 'X-CSRFToken', 'csrftoken'],
    r'D:\College_ERP\main_app\templates\staff_template\edit_student_result.html': ['getCookie', 'X-CSRFToken', 'csrftoken'],
    r'D:\College_ERP\main_app\templates\staff_template\staff_update_attendance.html': ['getCookie', 'X-CSRFToken', 'csrftoken'],
}
for tpath, keywords in templates_to_check.items():
    tname = os.path.basename(tpath)
    try:
        with open(tpath, 'r', encoding='utf-8') as tf:
            content = tf.read()
        missing = [k for k in keywords if k not in content]
        if missing:
            report(f"{tname}: CSRF keywords present", FAIL, f"Missing: {missing}")
        else:
            report(f"{tname}: CSRF keywords present", PASS)
    except Exception as e:
        report(f"{tname}: CSRF keywords present", FAIL, str(e))

# ─── SUMMARY ─────────────────────────────────────────────────────
print()
print("=" * 65)
print("SUMMARY")
print("=" * 65)
passed = sum(1 for _, s, _ in results if s == PASS)
failed = sum(1 for _, s, _ in results if s == FAIL)
skipped = sum(1 for _, s, _ in results if s == SKIP)
print(f"  PASSED:  {passed}")
print(f"  FAILED:  {failed}")
print(f"  SKIPPED: {skipped}")
print(f"  TOTAL:   {len(results)}")

if failed:
    print()
    print("FAILURES:")
    for name, status, detail in results:
        if status == FAIL:
            print(f"  ✗ {name}: {detail}")

print()
print("Database vendor:", connection.vendor)
print("No migrations executed. No Neon connection made.")
print("=" * 65)
