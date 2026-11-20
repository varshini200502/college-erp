"""
Phase 4 Acceptance Test Suite: Advanced Roles, Registrar & RBAC Isolation
"""
import sys, os
sys.path.insert(0, r'D:\College_ERP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django
django.setup()

from django.test import Client
from django.urls import reverse
from main_app.models import (
    CustomUser, Registrar, Staff, Department, HODAppointment, LeaveReportStaff
)
from main_app.views import get_role_home_url

PASS = "PASS"
FAIL = "FAIL"
results = []

def report(name, status, detail=""):
    results.append((name, status, detail))
    icon = "✓" if status == PASS else "✗"
    print(f"  [{icon}] {name}: {status}" + (f" — {detail}" if detail else ""))

print("=" * 65)
print("PHASE 4 ACCEPTANCE TEST SUITE")
print("=" * 65)

reg_user = CustomUser.objects.filter(email='registrar@college.edu').first()
admin_user = CustomUser.objects.filter(user_type=1).first()
student_user = CustomUser.objects.filter(user_type=3).first()
staff_user = CustomUser.objects.filter(user_type=2).first()

# ─── T1: Registrar Role & URL Resolution ──────────────────────
print("\n[T1] Registrar Role Configuration & Reverse Resolution")
try:
    if reg_user and str(reg_user.user_type) == '8':
        report("Registrar user exists with user_type=8", PASS)
    else:
        report("Registrar user exists with user_type=8", FAIL)

    home_url = get_role_home_url(8)
    if home_url == '/registrar/home/':
        report(f"Role 8 maps to correct home URL: {home_url}", PASS)
    else:
        report("Role 8 maps to correct home URL", FAIL, f"Got: {home_url}")
except Exception as e:
    report("Registrar role test", FAIL, str(e))

# ─── T2: Registrar Dashboard Access ───────────────────────────
print("\n[T2] Registrar Dashboard Web Access (HTTP 200)")
try:
    client = Client()
    client.force_login(reg_user)
    resp = client.get('/registrar/home/')
    if resp.status_code == 200:
        report("Registrar successfully loads /registrar/home/ (HTTP 200)", PASS)
    else:
        report("Registrar loads /registrar/home/", FAIL, f"Status: {resp.status_code}")

    resp2 = client.get('/registrar/appoint_hod/')
    if resp2.status_code == 200:
        report("Registrar loads /registrar/appoint_hod/ (HTTP 200)", PASS)
    else:
        report("Registrar loads /registrar/appoint_hod/", FAIL, f"Status: {resp2.status_code}")
except Exception as e:
    report("Registrar dashboard test", FAIL, str(e))

# ─── T3: RBAC Restrictions on Registrar Endpoints ─────────────
print("\n[T3] RBAC Protection on Registrar Views")
try:
    client_stu = Client()
    client_stu.force_login(student_user)
    resp_stu = client_stu.get('/registrar/home/')
    if resp_stu.status_code in [302, 403]:
        report("Student blocked from /registrar/home/ (redirected)", PASS)
    else:
        report("Student blocked from /registrar/home/", FAIL, f"Status: {resp_stu.status_code}")

    client_stf = Client()
    client_stf.force_login(staff_user)
    resp_stf = client_stf.get('/registrar/home/')
    if resp_stf.status_code in [302, 403]:
        report("Normal Staff blocked from /registrar/home/ (redirected)", PASS)
    else:
        report("Normal Staff blocked from /registrar/home/", FAIL, f"Status: {resp_stf.status_code}")
except Exception as e:
    report("RBAC restriction test", FAIL, str(e))

# ─── T4: Separation of Duties (Self-Approval Prohibited) ──────
print("\n[T4] Separation of Duties: Prohibition of Self-Approval on Leaves")
try:
    hod_appt = HODAppointment.objects.filter(is_active=True).first()
    hod_faculty = hod_appt.faculty
    hod_user = hod_faculty.admin

    # Create a staff leave application for the HOD
    leave = LeaveReportStaff.objects.create(
        staff=hod_faculty,
        date='2024-11-20',
        message='Annual medical checkup',
        status=0
    )

    # 1. HOD attempts to approve their own leave
    client_hod = Client()
    client_hod.force_login(hod_user)
    resp_self = client_hod.post('/staff/view/leave/', {'id': leave.id, 'status': '1'})
    if resp_self.status_code == 403:
        report("HOD self-approval of leave strictly blocked with HTTP 403", PASS)
    else:
        report("HOD self-approval of leave blocked", FAIL, f"Got status: {resp_self.status_code}")

    # 2. Administrator approves HOD's leave (cross-approval)
    client_admin = Client()
    client_admin.force_login(admin_user)
    resp_admin = client_admin.post('/staff/view/leave/', {'id': leave.id, 'status': '1'})
    leave.refresh_from_db()
    if leave.status == 1:
        report("Cross-approval by Admin successfully approved HOD leave", PASS)
    else:
        report("Cross-approval by Admin", FAIL, f"Status: {leave.status}")

    # Cleanup test leave
    leave.delete()
except Exception as e:
    report("Separation of duties test", FAIL, str(e))

# ─── T5: HOD Appointment via Registrar Portal ─────────────────
print("\n[T5] HOD Appointment Workflow via Registrar Portal")
try:
    dept_ece = Department.objects.get(code='ECE')
    faculty_candidate = Staff.objects.exclude(id=hod_faculty.id).first()

    client_reg = Client()
    client_reg.force_login(reg_user)
    resp_post = client_reg.post('/registrar/appoint_hod/', {
        'department_id': dept_ece.id,
        'faculty_id': faculty_candidate.id,
        'order_no': 'REG/APPT/ECE/2024/09',
        'start_date': '2024-11-17'
    }, follow=True)

    appt = HODAppointment.objects.filter(department=dept_ece, is_active=True).first()
    if appt and appt.faculty == faculty_candidate:
        report(f"Registrar appointed {faculty_candidate} as HOD of {dept_ece.name}", PASS)
    else:
        report("Registrar HOD appointment", FAIL, "Appointment not found")

    # Verify appointed faculty retains user_type=2
    if str(faculty_candidate.admin.user_type) == '2' and faculty_candidate.is_hod:
        report("Appointed HOD retains user_type=2 and dynamically inherits is_hod=True", PASS)
    else:
        report("Appointed HOD retains user_type=2", FAIL)
except Exception as e:
    report("Registrar HOD appointment test", FAIL, str(e))

# ─── SUMMARY ──────────────────────────────────────────────────
print()
print("=" * 65)
print("PHASE 4 SUMMARY")
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
    print("ALL PHASE 4 ACCEPTANCE TESTS PASSED!")
    sys.exit(0)
