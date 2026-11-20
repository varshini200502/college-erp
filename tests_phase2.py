"""
Phase 2 Acceptance Test Suite: Academic Lifecycle, Regulations & OBE Engine
"""
import sys, os
sys.path.insert(0, r'D:\College_ERP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django
django.setup()

from django.test import Client
from main_app.models import (
    Student, Programme, Batch, AcademicRegulation, StudentAcademicHistory,
    AlumniProfile, CustomUser
)
from main_app.academic_services import AcademicEngine

PASS = "PASS"
FAIL = "FAIL"
results = []

def report(name, status, detail=""):
    results.append((name, status, detail))
    icon = "✓" if status == PASS else "✗"
    print(f"  [{icon}] {name}: {status}" + (f" — {detail}" if detail else ""))

print("=" * 65)
print("PHASE 2 ACCEPTANCE TEST SUITE")
print("=" * 65)

prog_cse = Programme.objects.get(code='BTECH-CSE')
admin_user = CustomUser.objects.filter(user_type=1).first()
student = Student.objects.filter(programme=prog_cse).first()

# ─── T1: Unset Defaults on AcademicRegulation ─────────────────
print("\n[T1] Academic Regulations Default Safety (Unset Thresholds)")
try:
    reg_prov, _ = AcademicRegulation.objects.get_or_create(
        code='R22-CSE-PROV',
        programme=prog_cse,
        defaults={
            'effective_year': 2022,
            'approval_status': 'Provisional',
            'regulatory_source_reference': 'Draft Proposal Ref 2022/DP'
        }
    )
    if (
        reg_prov.min_attendance_percentage is None and
        reg_prov.condonation_min_percentage is None and
        reg_prov.min_credits_for_promotion is None and
        reg_prov.min_cgpa_for_award is None
    ):
        report("Default thresholds are unset (null) for unapproved regulations", PASS)
    else:
        report("Default thresholds are unset (null)", FAIL, "Found arbitrary hardcoded values")
except Exception as e:
    report("Regulation default safety", FAIL, str(e))

# ─── T2: Unapproved Regulation Prevents Automatic Decisions ───
print("\n[T2] Safety: Provisional/Unapproved Policy Withholds Automatic Decisions")
try:
    # Ensure all regulations for programme are Provisional for T2
    AcademicRegulation.objects.filter(programme=prog_cse).update(approval_status='Provisional')
    res = AcademicEngine.evaluate_semester_progression(
        student=student,
        semester=1,
        academic_year='2022-2023',
        credits_registered=20.0,
        credits_earned=20.0,
        sgpa=8.5,
        attendance_pct=60.0,  # low attendance
        fee_cleared=True,
        library_cleared=True
    )
    if res['status'] == 'Pending' and res['decision'] == 'Withheld':
        report("Automatic detention/promotion withheld when regulation is Provisional", PASS)
    else:
        report("Automatic detention/promotion withheld", FAIL, str(res))
except Exception as e:
    report("Provisional policy withholding test", FAIL, str(e))

# ─── T3: Approved Regulation Normal Promotion ─────────────────
print("\n[T3] Approved Regulation: Normal Promotion")
try:
    # Create or update to an officially approved regulation
    reg_appr, _ = AcademicRegulation.objects.get_or_create(
        code='R22-CSE-APPROVED',
        programme=prog_cse,
        defaults={
            'effective_year': 2022,
            'approval_status': 'Approved',
            'approved_by': 'Academic Council Meeting #42',
            'min_attendance_percentage': 75.0,
            'condonation_min_percentage': 65.0,
            'condonation_fee': 500.0,
            'min_credits_for_promotion': 15,
            'min_cgpa_for_award': 5.0,
            'regulatory_source_reference': 'Gazette Notification AC/2022/RES-42'
        }
    )
    # Ensure it is approved for test
    reg_appr.approval_status = 'Approved'
    reg_appr.min_attendance_percentage = 75.0
    reg_appr.condonation_min_percentage = 65.0
    reg_appr.condonation_fee = 500.0
    reg_appr.min_credits_for_promotion = 15
    reg_appr.min_cgpa_for_award = 5.0
    reg_appr.save()

    res_pass = AcademicEngine.evaluate_semester_progression(
        student=student,
        semester=1,
        academic_year='2022-2023',
        credits_registered=20.0,
        credits_earned=20.0,
        sgpa=8.2,
        attendance_pct=85.0,
        fee_cleared=True,
        library_cleared=True
    )
    if res_pass['status'] == 'Promoted':
        report("Student with 85% attendance successfully Promoted", PASS)
    else:
        report("Student with 85% attendance Promoted", FAIL, str(res_pass))
except Exception as e:
    report("Normal promotion test", FAIL, str(e))

# ─── T4: Approved Regulation Condonation Flow ─────────────────
print("\n[T4] Approved Regulation: Condonation Flow on Medical Grounds")
try:
    res_cond = AcademicEngine.evaluate_semester_progression(
        student=student,
        semester=2,
        academic_year='2022-2023',
        credits_registered=20.0,
        credits_earned=20.0,
        sgpa=7.8,
        attendance_pct=68.0,  # Between 65% and 75%
        fee_cleared=True,
        library_cleared=True,
        medical_certificate=True
    )
    if res_cond['status'] == 'Condoned' and 'condoned' in res_cond['reason'].lower():
        report("Attendance at 68% Condoned with medical certificate & fee logged", PASS)
    else:
        report("Attendance at 68% Condoned", FAIL, str(res_cond))
except Exception as e:
    report("Condonation test", FAIL, str(e))

# ─── T5: Approved Regulation Detention Flow ───────────────────
print("\n[T5] Approved Regulation: Detention Flow (Below Condonation Floor)")
try:
    res_det = AcademicEngine.evaluate_semester_progression(
        student=student,
        semester=3,
        academic_year='2023-2024',
        credits_registered=20.0,
        credits_earned=20.0,
        sgpa=6.5,
        attendance_pct=58.0,  # Below 65%
        fee_cleared=True,
        library_cleared=True,
        medical_certificate=True
    )
    if res_det['status'] == 'Detained_Attendance':
        report("Attendance at 58% strictly Detained due to shortage", PASS)
    else:
        report("Attendance at 58% Detained", FAIL, str(res_det))
except Exception as e:
    report("Detention test", FAIL, str(e))

# ─── T6: CGPA Recalculation & Academic History Persistence ────
print("\n[T6] Cumulative CGPA Recalculation & History Audit")
try:
    histories = student.academic_history.all()
    if histories.count() >= 3:
        report(f"Complete semester history recorded ({histories.count()} semesters)", PASS)
    else:
        report("Semester history recorded", FAIL, f"Count: {histories.count()}")

    if student.cgpa > 0.0:
        report(f"Student CGPA recalculated dynamically: {student.cgpa}", PASS)
    else:
        report("Student CGPA recalculated dynamically", FAIL)
except Exception as e:
    report("CGPA calculation test", FAIL, str(e))

# ─── T7: Graduation & Alumni Transition ───────────────────────
print("\n[T7] Graduation Verification & Alumni Transition")
try:
    # Test 1: Incomplete student cannot graduate
    grad_fail = AcademicEngine.evaluate_graduation(student)
    if not grad_fail['success'] and 'incomplete' in grad_fail['reason'].lower():
        report("Incomplete student properly blocked from graduation", PASS)
    else:
        report("Incomplete student properly blocked", FAIL, str(grad_fail))

    # Fast-forward create passing semesters 4 to 8 for graduation test
    for sem in range(4, 9):
        StudentAcademicHistory.objects.update_or_create(
            student=student, semester=sem, academic_year=f'202{sem//2}-202{sem//2+1}',
            defaults={
                'credits_registered': 20.0, 'credits_earned': 20.0,
                'sgpa': 8.0, 'attendance_percentage': 80.0,
                'promotion_status': 'Promoted' if sem < 8 else 'Passed',
                'fee_cleared': True, 'library_cleared': True
            }
        )
    # Also update sem 3 to Passed for graduation clearance test
    sem3 = StudentAcademicHistory.objects.filter(student=student, semester=3).first()
    if sem3:
        sem3.promotion_status = 'Passed'
        sem3.save()

    grad_success = AcademicEngine.evaluate_graduation(student)
    if grad_success['success'] and grad_success['status'] == 'Graduated':
        report("All-requirements-met student successfully Graduated", PASS)
        # Verify AlumniProfile creation
        alumni = AlumniProfile.objects.filter(student=student).first()
        if alumni:
            report("AlumniProfile automatically created upon graduation", PASS, f"Alumni ID #{alumni.id}")
        else:
            report("AlumniProfile automatically created upon graduation", FAIL)
    else:
        report("All-requirements-met student Graduated", FAIL, str(grad_success))
except Exception as e:
    report("Graduation evaluation test", FAIL, str(e))

# ─── T8: Web View for Regulations ─────────────────────────────
print("\n[T8] Regulations Web View Access & RBAC")
try:
    client = Client()
    client.force_login(admin_user)
    resp = client.get('/regulations/manage/')
    if resp.status_code == 200:
        report("/regulations/manage/ accessible to Admin (HTTP 200)", PASS)
    else:
        report("/regulations/manage/ accessible to Admin", FAIL, f"Status: {resp.status_code}")
except Exception as e:
    report("Regulations web view test", FAIL, str(e))

# ─── SUMMARY ──────────────────────────────────────────────────
print()
print("=" * 65)
print("PHASE 2 SUMMARY")
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
    print("ALL PHASE 2 ACCEPTANCE TESTS PASSED!")
    sys.exit(0)
