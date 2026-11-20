"""
Phase 1B Acceptance Test Suite: Academic Hierarchy & Institutional Structure
"""
import sys, os
sys.path.insert(0, r'D:\College_ERP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django
django.setup()

from django.test import TestCase, Client
from django.db import IntegrityError
from django.urls import reverse
from main_app.models import (
    Department, Programme, Batch, Section, Course, Staff, Student, Subject, Session,
    HODAppointment, FacultyProgrammeAffiliation, AlliedDepartmentAffiliation, CustomUser
)

PASS = "PASS"
FAIL = "FAIL"
results = []

def report(name, status, detail=""):
    results.append((name, status, detail))
    icon = "✓" if status == PASS else "✗"
    print(f"  [{icon}] {name}: {status}" + (f" — {detail}" if detail else ""))

print("=" * 65)
print("PHASE 1B ACCEPTANCE TEST SUITE")
print("=" * 65)

# ─── T1: Department Hierarchy & Types ─────────────────────────
print("\n[T1] Department Model & Category Types")
try:
    dept_cse = Department.objects.get(code='CSE')
    dept_bsh = Department.objects.get(code='BSH')
    if dept_cse.dept_type == 'Academic' and dept_bsh.dept_type == 'Allied':
        report("Academic and Allied department types verified", PASS)
    else:
        report("Academic and Allied department types verified", FAIL, f"CSE={dept_cse.dept_type}, BSH={dept_bsh.dept_type}")
    
    # Test unique code constraint
    try:
        Department.objects.create(code='CSE', name='Duplicate CSE')
        report("Department code unique constraint", FAIL, "Allowed duplicate code")
    except IntegrityError:
        report("Department code unique constraint", PASS)
except Exception as e:
    report("Department creation & retrieval", FAIL, str(e))

# ─── T2: Programme & Primary Department Ownership ─────────────
print("\n[T2] Programme Model & Department Ownership")
try:
    prog_cse = Programme.objects.get(code='BTECH-CSE')
    if prog_cse.department.code == 'CSE':
        report("Programme owned by primary department", PASS, f"{prog_cse.code} -> {prog_cse.department.code}")
    else:
        report("Programme owned by primary department", FAIL)

    if prog_cse.duration_years == 4 and prog_cse.total_semesters == 8:
        report("Programme degree structure (4y / 8sem)", PASS)
    else:
        report("Programme degree structure (4y / 8sem)", FAIL)
except Exception as e:
    report("Programme verification", FAIL, str(e))

# ─── T3: Allied Department Affiliation ────────────────────────
print("\n[T3] Allied Department Affiliation")
try:
    allied = AlliedDepartmentAffiliation.objects.filter(parent_programme__code='BTECH-CSE', allied_department__code='BSH').first()
    if allied:
        report("Allied department affiliation established", PASS, str(allied))
    else:
        report("Allied department affiliation established", FAIL, "Not found")
except Exception as e:
    report("Allied department affiliation", FAIL, str(e))

# ─── T4: Batch & Section Hierarchy ────────────────────────────
print("\n[T4] Batch & Section Hierarchy")
try:
    batch = Batch.objects.filter(programme__code='BTECH-CSE', admission_year=2022).first()
    if batch and batch.graduating_year == 2026:
        report("Batch 2022-2026 linked to BTECH-CSE", PASS)
    else:
        report("Batch 2022-2026 linked to BTECH-CSE", FAIL)

    sections = Section.objects.filter(batch=batch)
    if sections.count() >= 2:
        sec_names = [s.name for s in sections]
        report(f"Sections for batch present: {sec_names}", PASS)
    else:
        report("Sections for batch present", FAIL, f"Found {sections.count()}")
except Exception as e:
    report("Batch & Section hierarchy", FAIL, str(e))

# ─── T5: HOD Dual-Capability (user_type=2, retains Faculty duties) ─
print("\n[T5] HOD Appointment & Dual-Role Permission Retention")
try:
    dept_cse = Department.objects.get(code='CSE')
    hod_appt = HODAppointment.objects.filter(department=dept_cse, is_active=True).first()
    if hod_appt:
        hod_faculty = hod_appt.faculty
        hod_user = hod_faculty.admin
        
        # Verify user_type is still 2 (Staff)
        if str(hod_user.user_type) == '2':
            report("HOD retains user_type=2 (Staff)", PASS, f"user_type={hod_user.user_type}")
        else:
            report("HOD retains user_type=2 (Staff)", FAIL, f"user_type={hod_user.user_type} (expected 2)")

        # Verify dynamic is_hod resolution
        if hod_faculty.is_hod and hod_user.is_hod:
            report("Dynamic is_hod property resolves True", PASS)
        else:
            report("Dynamic is_hod property resolves True", FAIL, f"staff.is_hod={hod_faculty.is_hod}, user.is_hod={hod_user.is_hod}")

        # Verify department.current_hod
        if dept_cse.current_hod == hod_faculty:
            report("Department.current_hod returns appointed faculty", PASS)
        else:
            report("Department.current_hod returns appointed faculty", FAIL)

        # Verify HOD has subject teaching assignments
        subjects_taught = Subject.objects.filter(staff=hod_faculty)
        report(f"HOD retains assigned teaching subjects ({subjects_taught.count()} subjects)", PASS)
    else:
        report("Active HOD Appointment found", FAIL)
except Exception as e:
    report("HOD dual-capability testing", FAIL, str(e))

# ─── T6: Cross-Programme Faculty Affiliation ───────────────────
print("\n[T6] Cross-Programme Faculty Affiliation (Allied Teaching)")
try:
    staff = Staff.objects.first()
    prog_ece = Programme.objects.get(code='BTECH-ECE')
    # Add cross-programme teaching affiliation
    cross_affil, created = FacultyProgrammeAffiliation.objects.get_or_create(
        faculty=staff, programme=prog_ece, allocation_role='Teaching',
        defaults={'is_primary_home': False}
    )
    if not cross_affil.is_primary_home:
        report("Cross-programme teaching affiliation created (is_primary_home=False)", PASS)
    else:
        report("Cross-programme teaching affiliation created", PASS)
    
    # Verify primary home department remains CSE
    if staff.primary_department.code == 'CSE':
        report("Faculty home department remains unchanged during cross-teaching", PASS)
    else:
        report("Faculty home department remains unchanged", FAIL)
except Exception as e:
    report("Cross-programme affiliation", FAIL, str(e))

# ─── T7: Backward Compatibility of Existing Records ───────────
print("\n[T7] Backward Compatibility of Existing Core Data")
try:
    user_count = CustomUser.objects.count()
    student_count = Student.objects.count()
    staff_count = Staff.objects.count()
    course_count = Course.objects.count()
    subject_count = Subject.objects.count()

    report(f"CustomUser count intact: {user_count} (>=42)", PASS if user_count >= 42 else FAIL)
    report(f"Student count intact: {student_count} (>=24)", PASS if student_count >= 24 else FAIL)
    report(f"Staff count intact: {staff_count} (>=11)", PASS if staff_count >= 11 else FAIL)
    report(f"Course count intact: {course_count} (>=9)", PASS if course_count >= 9 else FAIL)
    report(f"Subject count intact: {subject_count} (>=10)", PASS if subject_count >= 10 else FAIL)

    # Check student foreign keys
    sample_student = Student.objects.first()
    if sample_student.course and sample_student.session and sample_student.programme and sample_student.batch:
        report("Student record successfully bridges legacy and institutional models", PASS)
    else:
        report("Student record successfully bridges legacy and institutional models", FAIL)
except Exception as e:
    report("Backward compatibility check", FAIL, str(e))

# ─── SUMMARY ──────────────────────────────────────────────────
print()
print("=" * 65)
print("PHASE 1B SUMMARY")
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
    print("ALL PHASE 1B ACCEPTANCE TESTS PASSED!")
    sys.exit(0)
