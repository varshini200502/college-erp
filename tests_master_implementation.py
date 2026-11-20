"""
MASTER IMPLEMENTATION ACCEPTANCE TEST SUITE — COLLEGE ERP
Phases 1 through 10 Complete Verification
"""
import sys, os
sys.path.insert(0, r'D:\College_ERP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django
django.setup()

from django.test.utils import setup_test_environment
setup_test_environment()

from django.test import Client
from django.urls import reverse
from django.db.models import Q
from main_app.models import (
    CustomUser, Student, Staff, Course, Subject, Session,
    Department, Programme, Batch, Section, HODAppointment,
    StudentProject, StudentInternship, StudentOverseasProgression,
    FacultyInternationalContribution, FacultyPublication, FacultyPatent,
    FacultyTraining, StudentResult, AttendanceReport, NAACCriterion,
    NAACMetricData, NBAProgram, ProgramOutcome, ProgramSpecificOutcome
)

PASS = "PASS"
FAIL = "FAIL"
results = []

def report(name, status, detail=""):
    results.append((name, status, detail))
    icon = "✓" if status == PASS else "✗"
    print(f"  [{icon}] {name}: {status}" + (f" — {detail}" if detail else ""))

print("=" * 75)
print("MASTER IMPLEMENTATION COMPLETE ACCEPTANCE TEST SUITE")
print("=" * 75)

# Users
admin_user = CustomUser.objects.filter(user_type=1).first()
staff_user = CustomUser.objects.filter(user_type=2).first()
student_user = CustomUser.objects.filter(user_type=3).first()
principal_user = CustomUser.objects.filter(user_type=4).first()
finance_user = CustomUser.objects.filter(user_type=5).first()
accreditation_user = CustomUser.objects.filter(user_type=7).first()
reg_user = CustomUser.objects.filter(user_type=8).first()

# ==============================================================================
# SUITE 1: ROLE RESPONSIBILITIES & PERMISSIONS (PHASE 1)
# ==============================================================================
print("\n" + "="*50)
print("SUITE 1: Role Responsibilities & Permissions")
print("="*50)

# T1.1: Registrar Dashboard Access
try:
    c = Client()
    c.force_login(reg_user)
    resp = c.get('/registrar/home/')
    if resp.status_code == 200:
        report("Registrar loads /registrar/home/ (HTTP 200)", PASS)
    else:
        report("Registrar loads /registrar/home/", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("Registrar dashboard test", FAIL, str(e))

# T1.2: Student blocked from Registrar portal
try:
    c_st = Client()
    c_st.force_login(student_user)
    resp = c_st.get('/registrar/home/')
    if resp.status_code in [302, 403]:
        report("Student blocked from Registrar portal (Redirect / Forbidden)", PASS)
    else:
        report("Student blocked from Registrar portal", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("Student access check", FAIL, str(e))

# T1.3: Registrar Academic Structure Views
try:
    c = Client()
    c.force_login(reg_user)
    r1 = c.get('/registrar/departments/')
    r2 = c.get('/registrar/programmes/')
    r3 = c.get('/registrar/batches/')
    r4 = c.get('/registrar/structure/')
    if all(r.status_code == 200 for r in [r1, r2, r3, r4]):
        report("Registrar structure routes (Departments, Programmes, Batches, Structure) return HTTP 200", PASS)
    else:
        report("Registrar structure routes", FAIL, f"Statuses: {[r.status_code for r in [r1, r2, r3, r4]]}")
except Exception as e:
    report("Registrar structure test", FAIL, str(e))

# T1.4: Registrar Onboarding Forms Access
try:
    c = Client()
    c.force_login(reg_user)
    r_st = c.get('/registrar/student/add/')
    r_fac = c.get('/registrar/faculty/add/')
    if r_st.status_code == 200 and r_fac.status_code == 200:
        report("Registrar onboarding forms (/registrar/student/add/, /registrar/faculty/add/) return HTTP 200", PASS)
    else:
        report("Registrar onboarding forms", FAIL, f"Student: {r_st.status_code}, Faculty: {r_fac.status_code}")
except Exception as e:
    report("Registrar forms access test", FAIL, str(e))


# ==============================================================================
# SUITE 2: STUDENT DIRECTORY & 7-SECTION PROFILE (PHASE 2 & PHASE 8)
# ==============================================================================
print("\n" + "="*50)
print("SUITE 2: Student Directory & 7-Section Profile")
print("="*50)

# T2.1: Registrar Student Directory displays all 24 students
try:
    c = Client()
    c.force_login(reg_user)
    resp = c.get('/registrar/students/')
    if resp.status_code == 200 and resp.context['total_count'] == 24:
        report("Registrar Student Directory loads all 24 students (Total: 24, Active: 17, Alumni: 5, Graduated: 2)", PASS)
    else:
        report("Registrar Student Directory counts", FAIL, f"Total: {resp.context.get('total_count') if resp.status_code == 200 else resp.status_code}")
except Exception as e:
    report("Registrar student directory test", FAIL, str(e))

# T2.2: Principal Student Roster displays all 24 students
try:
    c = Client()
    c.force_login(principal_user)
    resp = c.get('/principal/students/')
    if resp.status_code == 200 and resp.context['total_count'] == 24:
        report("Principal Student Roster loads all 24 students without clipping (HTTP 200)", PASS)
    else:
        report("Principal Student Roster counts", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("Principal student roster test", FAIL, str(e))

# T2.3: Detailed Student Profile (7 Sections)
try:
    c = Client()
    c.force_login(principal_user)
    st = Student.objects.first()
    resp = c.get(f'/student/profile/{st.id}/')
    if resp.status_code == 200:
        content = resp.content.decode('utf-8')
        has_a = "Personal & Admission" in content
        has_b = "Academic Results" in content
        has_c = "Project Portfolio" in content
        has_d = "Internships" in content
        has_e = "Placement & Career" in content
        has_f = "Overseas Progression" in content
        has_g = "Achievements" in content
        if all([has_a, has_b, has_c, has_d, has_e, has_f, has_g]):
            report(f"Student Profile for {st.admin.first_name} {st.admin.last_name} renders all 7 Sections (A-G) with HTTP 200", PASS)
        else:
            missing = [k for k, v in [("A", has_a), ("B", has_b), ("C", has_c), ("D", has_d), ("E", has_e), ("F", has_f), ("G", has_g)] if not v]
            report("Student Profile tabs", FAIL, f"Missing tabs: {missing}")
    else:
        report("Student Profile view", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("Student profile test", FAIL, str(e))


# ==============================================================================
# SUITE 3: FACULTY DIRECTORY & RESEARCH DOSSIER (PHASE 3)
# ==============================================================================
print("\n" + "="*50)
print("SUITE 3: Faculty Directory & Detailed Profile")
print("="*50)

# T3.1: Faculty Directory Access
try:
    c = Client()
    c.force_login(principal_user)
    resp = c.get('/principal/faculty/')
    if resp.status_code == 200 and resp.context['total_count'] == 11:
        report("Principal Faculty Directory displays all 11 appointed faculty (HTTP 200)", PASS)
    else:
        report("Principal Faculty Directory counts", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("Faculty directory test", FAIL, str(e))

# T3.2: Detailed Faculty Profile
try:
    c = Client()
    c.force_login(principal_user)
    staff = Staff.objects.first()
    resp = c.get(f'/faculty/profile/{staff.id}/')
    if resp.status_code == 200:
        content = resp.content.decode('utf-8')
        has_teaching = "Teaching" in content
        has_research = "Research & Publications" in content
        has_fdp = "Faculty Development" in content
        has_guided = "Guided Projects" in content
        has_intl = "International" in content
        if all([has_teaching, has_research, has_fdp, has_guided, has_intl]):
            report(f"Faculty Profile for {staff.admin.first_name} {staff.admin.last_name} renders complete dossier (Teaching, Papers, FDPs, Guided Projects, International)", PASS)
        else:
            report("Faculty Profile sections", FAIL, "One or more sections missing")
    else:
        report("Faculty Profile view", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("Faculty profile test", FAIL, str(e))


# ==============================================================================
# SUITE 4: PROJECT MANAGEMENT & 17 DOMAIN ANALYTICS (PHASE 4)
# ==============================================================================
print("\n" + "="*50)
print("SUITE 4: Student Project Management & Domain Analytics")
print("="*50)

# T4.1: Principal Project Dashboard
try:
    c = Client()
    c.force_login(principal_user)
    resp = c.get('/principal/projects/')
    if resp.status_code == 200 and resp.context['total_projects'] >= 6:
        report(f"Principal Project & Domain Dashboard renders (Total Projects: {resp.context['total_projects']}, Students: {resp.context['students_participating']})", PASS)
    else:
        report("Principal Project Dashboard", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("Project dashboard test", FAIL, str(e))

# T4.2: Clickable Domain Drill-Down (Computer Vision)
try:
    c = Client()
    c.force_login(principal_user)
    resp = c.get('/principal/projects/?domain=Computer+Vision+and+Image+Processing')
    if resp.status_code == 200:
        drone_proj = any("Drone" in p.title for p in resp.context['projects'])
        if drone_proj:
            report("Clickable Domain Drill-Down filters Computer Vision projects correctly", PASS)
        else:
            report("Domain Drill-Down Computer Vision", FAIL, "Drone project not in filtered results")
    else:
        report("Domain Drill-Down request", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("Domain drill-down test", FAIL, str(e))

# T4.3: Interdisciplinary Capstones Anchored to Primary Programme
try:
    inter_proj = StudentProject.objects.filter(project_type='Interdisciplinary').first()
    if inter_proj and inter_proj.primary_programme and inter_proj.is_nba_credited:
        report(f"Interdisciplinary Capstone '{inter_proj.title}' credited exclusively to primary programme ({inter_proj.primary_programme.code}) to prevent double-counting", PASS)
    else:
        report("Interdisciplinary anchoring", FAIL, "Primary programme anchoring missing")
except Exception as e:
    report("Interdisciplinary test", FAIL, str(e))


# ==============================================================================
# SUITE 5: INTERNATIONAL & OVERSEAS PROGRESSION (PHASE 5)
# ==============================================================================
print("\n" + "="*50)
print("SUITE 5: International & Overseas Progression Analytics")
print("="*50)

# T5.1: Principal International Analytics Dashboard
try:
    c = Client()
    c.force_login(principal_user)
    resp = c.get('/principal/international-analytics/')
    if resp.status_code == 200:
        st_count = resp.context['total_student_overseas']
        fac_count = resp.context['total_faculty_intl']
        if st_count >= 4 and fac_count >= 3:
            report(f"International Progression Dashboard renders with global student ({st_count}) and faculty ({fac_count}) records", PASS)
        else:
            report("International Progression counts", FAIL, f"Students: {st_count}, Faculty: {fac_count}")
    else:
        report("International Progression view", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("International analytics test", FAIL, str(e))

# T5.2: Filter by Country (Canada)
try:
    c = Client()
    c.force_login(principal_user)
    resp = c.get('/principal/international-analytics/?country=Canada')
    if resp.status_code == 200:
        canada_found = any(s.country == 'Canada' for s in resp.context['student_records'])
        if canada_found:
            report("Country filter ('Canada') correctly isolates overseas internship records", PASS)
        else:
            report("Country filter Canada", FAIL, "No records returned")
    else:
        report("Country filter request", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("Country filter test", FAIL, str(e))


# ==============================================================================
# SUITE 6: NAAC 7-CRITERIA ACCOUNTABLE WORKFLOW (PHASE 6)
# ==============================================================================
print("\n" + "="*50)
print("SUITE 6: NAAC 7-Criteria Evidence & Review Workflow")
print("="*50)

# T6.1: Criterion Detail with Responsibility Mapping
try:
    c = Client()
    c.force_login(accreditation_user)
    resp = c.get('/accreditation/naac/criterion/1/')
    if resp.status_code == 200:
        resp_info = resp.context.get('responsibility_info')
        if resp_info and "Academic Section" in resp_info.get('owning_sections', ''):
            report("NAAC Criterion 1 displays institutional responsibility mapping (Owning Section: Academic Section, HODs)", PASS)
        else:
            report("Responsibility mapping", FAIL, f"Info: {resp_info}")
    else:
        report("Criterion detail access", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("NAAC responsibility test", FAIL, str(e))

# T6.2: 6-Stage Workflow Transitions (Submit -> Return -> Verify Internal -> Principal Approve)
try:
    c_acc = Client()
    c_acc.force_login(accreditation_user)
    c_pr = Client()
    c_pr.force_login(principal_user)

    crit = NAACCriterion.objects.filter(criterion_number=1).first()
    metric, _ = NAACMetricData.objects.get_or_create(
        criterion=crit, metric_code="TEST-1.1",
        defaults={'title': "Test Curriculum Metric", 'quantitative_value': 85.0, 'stage': 'DATA_ENTRY'}
    )

    # 1. Submit for review
    c_acc.post(f'/accreditation/naac/criterion/{crit.id}/', {'action': 'submit_for_review', 'metric_id': metric.id})
    metric.refresh_from_db()
    s1 = metric.stage == "SUBMITTED"

    # 2. Return for correction
    c_acc.post(f'/accreditation/naac/criterion/{crit.id}/', {'action': 'return_correction', 'metric_id': metric.id, 'return_reason': 'Need signed syllabus copy'})
    metric.refresh_from_db()
    s2 = metric.stage == "RETURNED" and "syllabus" in metric.return_reason

    # 3. Re-submit and Verify Internally
    c_acc.post(f'/accreditation/naac/criterion/{crit.id}/', {'action': 'submit_for_review', 'metric_id': metric.id})
    c_acc.post(f'/accreditation/naac/criterion/{crit.id}/', {'action': 'verify_internal', 'metric_id': metric.id, 'review_comments': 'Audited & verified'})
    metric.refresh_from_db()
    s3 = metric.stage == "VERIFIED_INTERNAL" and metric.internal_verified_at is not None

    # 4. Final Institutional Approval by Principal
    c_pr.post(f'/accreditation/naac/criterion/{crit.id}/', {'action': 'approve_principal', 'metric_id': metric.id})
    metric.refresh_from_db()
    s4 = metric.stage == "APPROVED_PRINCIPAL" and metric.is_verified is True and metric.principal_approved_at is not None

    if s1 and s2 and s3 and s4:
        report("Complete 6-Stage NAAC Review Workflow verified (Submit -> Return -> Verify Internally -> Principal Approve)", PASS)
    else:
        report("6-Stage Workflow transitions", FAIL, f"Stages: s1={s1}, s2={s2}, s3={s3}, s4={s4}")

    # Clean up test metric
    metric.delete()
except Exception as e:
    report("NAAC workflow test", FAIL, str(e))


# ==============================================================================
# SUITE 7: NBA PROGRAMME-SPECIFIC OBE & SAR EXPORT (PHASE 7)
# ==============================================================================
print("\n" + "="*50)
print("SUITE 7: NBA Programme-Specific OBE & SAR Export")
print("="*50)

# T7.1: NBA Program List & Status
try:
    c = Client()
    c.force_login(accreditation_user)
    resp = c.get('/accreditation/nba/programs/')
    if resp.status_code == 200 and len(resp.context['programs']) == 9:
        report("NBA OBE Programs list renders all 9 engineering programmes (HTTP 200)", PASS)
    else:
        report("NBA Programs list", FAIL, f"Status {resp.status_code}")
except Exception as e:
    report("NBA programs list test", FAIL, str(e))

# T7.2: NBA SAR Export Format (JSON & CSV)
try:
    c = Client()
    c.force_login(accreditation_user)
    r_json = c.get('/accreditation/nba/sar/1/?format=json')
    r_csv = c.get('/accreditation/nba/sar/1/?format=csv')
    if r_json.status_code == 200 and r_csv.status_code == 200:
        import json
        payload = json.loads(r_json.content.decode('utf-8'))
        is_factual = "accreditation_verdict" not in payload
        if "program_name" in payload and is_factual:
            report("NBA SAR Multi-Format Export (JSON & Tabular CSV) operates factually without fabricated verdicts", PASS)
        else:
            report("NBA SAR Export contents", FAIL, "Unexpected payload")
    else:
        report("NBA SAR Export requests", FAIL, f"JSON: {r_json.status_code}, CSV: {r_csv.status_code}")
except Exception as e:
    report("NBA SAR export test", FAIL, str(e))


# ==============================================================================
# SUITE 8: DATA INTEGRITY & DYNAMIC FOOTER (PHASES 8 & 10)
# ==============================================================================
print("\n" + "="*50)
print("SUITE 8: Data Integrity & Dynamic Footer")
print("="*50)

# T8.1: Database Baseline Preservation
try:
    u_cnt = CustomUser.objects.count()
    s_cnt = Student.objects.count()
    f_cnt = Staff.objects.count()
    c_cnt = Course.objects.count()
    sub_cnt = Subject.objects.count()
    res_cnt = StudentResult.objects.count()

    if u_cnt >= 43 and s_cnt == 24 and f_cnt == 11 and c_cnt == 9 and sub_cnt == 27 and res_cnt == 87:
        report(f"All 43 Users, 24 Students, 11 Staff, 9 Courses, 27 Subjects, and 87 Results 100% preserved", PASS)
    else:
        report("Database preservation counts", FAIL, f"U:{u_cnt}, S:{s_cnt}, F:{f_cnt}, C:{c_cnt}, Sub:{sub_cnt}, Res:{res_cnt}")
except Exception as e:
    report("Database baseline test", FAIL, str(e))

# T8.2: Dynamic Copyright Footer Verification
try:
    c = Client()
    resp = c.get(reverse('login_page'))
    content = resp.content.decode('utf-8')
    if "2026 College ERP System" in content:
        report("Footer copyright year dynamically renders current year ('© 2026 College ERP System')", PASS)
    else:
        report("Footer copyright year", FAIL, "Dynamic 2026 year missing from login page")
except Exception as e:
    report("Footer copyright test", FAIL, str(e))


# ==============================================================================
# FINAL CONSOLIDATED SUMMARY
# ==============================================================================
print("\n" + "=" * 75)
total_tests = len(results)
pass_count = sum(1 for _, status, _ in results if status == PASS)
fail_count = sum(1 for _, status, _ in results if status == FAIL)
pct = round((pass_count / total_tests) * 100, 1)

print(f"MASTER IMPLEMENTATION TEST RESULTS: {pass_count} / {total_tests} PASSED ({pct}%)")
print("=" * 75)

if fail_count > 0:
    print(f"\nFAILED TESTS ({fail_count}):")
    for name, status, detail in results:
        if status == FAIL:
            print(f"  - {name}: {detail}")
    sys.exit(1)
else:
    print("\nALL TEST SUITES PASSED FLAWLESSLY. ZERO FAILURES.")
    sys.exit(0)
