"""
Phase 5 Acceptance Test Suite: Continuous Assessment, Project & Research Portfolios
"""
import sys, os
sys.path.insert(0, r'D:\College_ERP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django
django.setup()

from django.test import Client
from main_app.models import (
    StudentProject, Staff, Student, Programme,
    FacultyPublication, FacultyPatent, FacultyTraining, CustomUser
)
from main_app.project_services import ProjectService

PASS = "PASS"
FAIL = "FAIL"
results = []

def report(name, status, detail=""):
    results.append((name, status, detail))
    icon = "✓" if status == PASS else "✗"
    print(f"  [{icon}] {name}: {status}" + (f" — {detail}" if detail else ""))

print("=" * 65)
print("PHASE 5 ACCEPTANCE TEST SUITE")
print("=" * 65)

admin_user = CustomUser.objects.filter(user_type=1).first()
prog_cse = Programme.objects.get(code='BTECH-CSE')
prog_ece = Programme.objects.get(code='BTECH-ECE')
staff_cse = Staff.objects.filter(primary_department__code='CSE').first()
staff_ece = Staff.objects.exclude(id=staff_cse.id).first()
students = Student.objects.all()[:3]
student_ids = [s.id for s in students]

# ─── T1: Major Capstone Project Creation ───────────────────────
print("\n[T1] Major Capstone Project Creation & Student Team Linking")
try:
    proj_major = ProjectService.create_project(
        title="Autonomous Drone Vision Navigation",
        project_type="Major",
        academic_year="2024-2025",
        primary_programme=prog_cse,
        guide=staff_cse,
        student_ids=student_ids,
        abstract="Deep learning vision pipeline for real-time indoor obstacle avoidance."
    )
    if proj_major and proj_major.students.count() == len(student_ids):
        report(f"Major Project created with {proj_major.students.count()} team members", PASS)
    else:
        report("Major Project created", FAIL)
except Exception as e:
    report("Major project creation test", FAIL, str(e))

# ─── T2: Interdisciplinary Project Creation ───────────────────
print("\n[T2] Interdisciplinary Capstone Project (Primary + Secondary Departments)")
try:
    proj_inter = ProjectService.create_project(
        title="Smart Grid IoT Energy Harvesting & Edge AI",
        project_type="Interdisciplinary",
        academic_year="2024-2025",
        primary_programme=prog_cse,
        secondary_programme=prog_ece,
        guide=staff_cse,
        co_guide=staff_ece,
        student_ids=[student_ids[0]],
        abstract="Collaborative edge-computing smart grid monitoring across CSE and ECE."
    )
    if proj_inter.primary_programme == prog_cse and proj_inter.secondary_programme == prog_ece:
        report(f"Interdisciplinary project anchored: Primary={prog_cse.code}, Allied={prog_ece.code}", PASS)
    else:
        report("Interdisciplinary project anchor", FAIL)
except Exception as e:
    report("Interdisciplinary project test", FAIL, str(e))

# ─── T3: Prevention of Double-Counting in NBA Metrics ─────────
print("\n[T3] Strict Prevention of NBA Project Double-Counting")
try:
    cse_nba_projects = ProjectService.get_programme_nba_projects(prog_cse, "2024-2025")
    ece_nba_projects = ProjectService.get_programme_nba_projects(prog_ece, "2024-2025")

    # Project should be counted under CSE (primary)
    cse_has_project = cse_nba_projects.filter(id=proj_inter.id).exists()
    # Project should NOT be counted under ECE (secondary)
    ece_has_project = ece_nba_projects.filter(id=proj_inter.id).exists()

    if cse_has_project and not ece_has_project:
        report("Interdisciplinary project credited exclusively to Primary Department (No double-counting)", PASS)
    else:
        report("Double-counting prevention", FAIL, f"CSE={cse_has_project}, ECE={ece_has_project} (expected CSE=True, ECE=False)")
except Exception as e:
    report("Double-counting prevention test", FAIL, str(e))

# ─── T4: Rubric Evaluation & Automatic Total Calculation ───────
print("\n[T4] Project Rubric Evaluation & Total Recalculation")
try:
    total = ProjectService.record_rubric_evaluation(
        project=proj_major,
        review1_score=24.5,
        review2_score=25.0,
        final_score=42.5
    )
    proj_major.refresh_from_db()
    if proj_major.total_score == 92.0 and total == 92.0:
        report(f"Rubric scores aggregated: 24.5 + 25.0 + 42.5 = {proj_major.total_score} / 100", PASS)
    else:
        report("Rubric score aggregation", FAIL, f"Total={proj_major.total_score} (expected 92.0)")
except Exception as e:
    report("Rubric evaluation test", FAIL, str(e))

# ─── T5: Faculty Scholarly Portfolio Aggregation ──────────────
print("\n[T5] Faculty Research & Scholarly Portfolio Aggregation")
try:
    # Seed a publication and patent for staff_cse
    pub, _ = FacultyPublication.objects.get_or_create(
        staff=staff_cse,
        title="Reinforcement Learning for Edge Computing Networks",
        defaults={
            'journal_or_conference_name': 'IEEE Transactions on Computers',
            'publication_date': '2024-03-15',
            'indexing': 'Scopus',
            'doi': '10.1109/TC.2024.1234567'
        }
    )
    pat, _ = FacultyPatent.objects.get_or_create(
        staff=staff_cse,
        title="Edge Computing Hardware Accelerator Device",
        defaults={
            'application_number': 'IN202441012345',
            'status': 'Granted',
            'patent_office': 'Indian Patent Office'
        }
    )

    portfolio = ProjectService.get_faculty_research_portfolio(staff_cse)
    if portfolio['total_publications'] >= 1 and portfolio['scopus_count'] >= 1:
        report(f"Publications captured: {portfolio['total_publications']} (Scopus: {portfolio['scopus_count']})", PASS)
    else:
        report("Publications captured", FAIL)

    if portfolio['total_patents'] >= 1 and portfolio['granted_patents'] >= 1:
        report(f"Patents captured: {portfolio['total_patents']} (Granted: {portfolio['granted_patents']})", PASS)
    else:
        report("Patents captured", FAIL)

    if portfolio['guided_projects_count'] >= 1:
        report(f"Guided Capstone Projects captured: {portfolio['guided_projects_count']}", PASS)
    else:
        report("Guided projects captured", FAIL)
except Exception as e:
    report("Faculty research portfolio test", FAIL, str(e))

# ─── T6: Project Management Web View ──────────────────────────
print("\n[T6] Project Management Web View Access & Rendering")
try:
    client = Client()
    client.force_login(admin_user)
    resp = client.get('/projects/manage/')
    if resp.status_code == 200:
        report("/projects/manage/ rendered successfully (HTTP 200)", PASS)
    else:
        report("/projects/manage/ rendered", FAIL, f"Status: {resp.status_code}")
except Exception as e:
    report("Project management web view test", FAIL, str(e))

# ─── SUMMARY ──────────────────────────────────────────────────
print()
print("=" * 65)
print("PHASE 5 SUMMARY")
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
    print("ALL PHASE 5 ACCEPTANCE TESTS PASSED!")
    sys.exit(0)
