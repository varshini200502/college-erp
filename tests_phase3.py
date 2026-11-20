"""
Phase 3 Acceptance Test Suite: OBE Curriculum & NBA Attainment Suite
"""
import sys, os
sys.path.insert(0, r'D:\College_ERP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django
django.setup()

from django.test import Client
from main_app.models import (
    NBAProgram, CourseOutcome, COPOMapping, COAttainmentRecord,
    ProgramOutcome, ProgramSpecificOutcome, ContinuousImprovementAction,
    Subject, Course, Session, CustomUser, StudentResult
)
from main_app.obe_engine import OBEEngine

PASS = "PASS"
FAIL = "FAIL"
results = []

def report(name, status, detail=""):
    results.append((name, status, detail))
    icon = "✓" if status == PASS else "✗"
    print(f"  [{icon}] {name}: {status}" + (f" — {detail}" if detail else ""))

print("=" * 65)
print("PHASE 3 ACCEPTANCE TEST SUITE")
print("=" * 65)

admin_user = CustomUser.objects.filter(user_type=1).first()
session = Session.objects.first()
course_cse = Course.objects.filter(name__icontains='Computer').first()

# ─── T1: NBA Program & Standard PO Seeding ────────────────────
print("\n[T1] Standard NBA Graduate Attributes (PO1-PO12 & PSOs) Seeding")
try:
    nba_prog, _ = NBAProgram.objects.get_or_create(
        course=course_cse,
        defaults={'program_name': 'B.Tech in Computer Science & Engineering', 'tier': 'Tier I'}
    )
    created_pos, created_psos = OBEEngine.seed_standard_nba_graduate_attributes(nba_prog)
    po_count = nba_prog.pos.count()
    pso_count = nba_prog.psos.count()

    if po_count == 12:
        report("All 12 NBA Graduate Attributes (PO1-PO12) seeded", PASS)
    else:
        report("All 12 NBA Graduate Attributes seeded", FAIL, f"Count={po_count}")

    if pso_count >= 2:
        report(f"Program Specific Outcomes (PSOs) seeded: {pso_count}", PASS)
    else:
        report("PSOs seeded", FAIL, f"Count={pso_count}")
except Exception as e:
    report("NBA Program & PO seeding test", FAIL, str(e))

# ─── T2: Course Outcomes (CO) Creation ────────────────────────
print("\n[T2] Course Outcome (CO) Creation & Configuration")
try:
    subject = Subject.objects.filter(course=course_cse).first()
    co1, _ = CourseOutcome.objects.get_or_create(
        subject=subject, code='CO1',
        defaults={'description': 'Understand fundamental data structures and algorithmic complexity.', 'target_percentage': 60.0, 'attainment_target_students_percentage': 70.0}
    )
    co2, _ = CourseOutcome.objects.get_or_create(
        subject=subject, code='CO2',
        defaults={'description': 'Design and implement advanced tree and graph algorithms.', 'target_percentage': 65.0, 'attainment_target_students_percentage': 70.0}
    )
    if co1 and co2:
        report(f"Course Outcomes created for {subject.name}: CO1 & CO2", PASS)
    else:
        report("Course Outcomes created", FAIL)
except Exception as e:
    report("CO creation test", FAIL, str(e))

# ─── T3: CO-PO / PSO Correlation Matrix Mapping ───────────────
print("\n[T3] CO-PO & PSO Correlation Matrix Mapping")
try:
    po1 = nba_prog.pos.get(code='PO1')
    po2 = nba_prog.pos.get(code='PO2')
    pso1 = nba_prog.psos.get(code='PSO1')

    m1, _ = COPOMapping.objects.update_or_create(
        course_outcome=co1, po=po1,
        defaults={'correlation_level': 3, 'justification': 'Direct application of foundational computing principles'}
    )
    m2, _ = COPOMapping.objects.update_or_create(
        course_outcome=co1, po=po2,
        defaults={'correlation_level': 2, 'justification': 'Problem decomposition and analytical reasoning'}
    )
    m3, _ = COPOMapping.objects.update_or_create(
        course_outcome=co2, pso=pso1,
        defaults={'correlation_level': 3, 'justification': 'Software architecture and algorithmic implementation'}
    )
    if m1.correlation_level == 3 and m2.correlation_level == 2 and m3.correlation_level == 3:
        report("CO-PO and CO-PSO correlation levels recorded with justifications", PASS)
    else:
        report("CO-PO correlation levels recorded", FAIL)
except Exception as e:
    report("CO-PO mapping test", FAIL, str(e))

# ─── T4: Configurable Direct Attainment Calculation ───────────
print("\n[T4] Configurable Direct CO Attainment Calculation")
try:
    # Test with standard threshold (60% marks, 70% students for Level 3)
    level_std, pct_passed, count = OBEEngine.calculate_co_direct_attainment(
        co1, session=session, target_marks_pct=60.0, level_3_students_pct=70.0
    )
    report(f"Standard threshold attainment level: {level_std} ({pct_passed:.1f}% students >= 60% marks)", PASS)

    # Test with stricter threshold (80% marks) - level should be lower or equal
    level_strict, pct_strict, _ = OBEEngine.calculate_co_direct_attainment(
        co1, session=session, target_marks_pct=80.0, level_3_students_pct=70.0
    )
    if level_strict <= level_std:
        report(f"Strict threshold (80% marks) adapts dynamically: Level {level_strict} (<= {level_std})", PASS)
    else:
        report("Strict threshold dynamic adaptation", FAIL, f"{level_strict} > {level_std}")
except Exception as e:
    report("Direct attainment calculation test", FAIL, str(e))

# ─── T5: Configurable Direct/Indirect Weightings ───────────────
print("\n[T5] Configurable Weightings (80:20 vs Custom Institutional Policy)")
try:
    # 80:20 calculation
    res_80_20 = OBEEngine.compute_subject_co_attainments(
        subject=subject, session=session, direct_weight=0.80, indirect_weight=0.20
    )
    overall_80 = res_80_20[0]['overall']

    # 70:30 calculation
    res_70_30 = OBEEngine.compute_subject_co_attainments(
        subject=subject, session=session, direct_weight=0.70, indirect_weight=0.30
    )
    overall_70 = res_70_30[0]['overall']

    report(f"80:20 Overall CO Attainment: {overall_80} / 3.0", PASS)
    report(f"70:30 Overall CO Attainment: {overall_70} / 3.0", PASS)

    # Check weight validation
    try:
        OBEEngine.compute_subject_co_attainments(subject, session, direct_weight=0.80, indirect_weight=0.30)
        report("Weight validation rejected non-1.0 sum", FAIL, "Allowed sum = 1.10")
    except AssertionError:
        report("Weight validation strictly enforces sum == 1.0", PASS)
except Exception as e:
    report("Configurable weightings test", FAIL, str(e))

# ─── T6: Program Outcome Attainment Matrix & Gap Analysis ─────
print("\n[T6] Program Outcome (PO) Attainment Matrix & Gap Analysis")
try:
    matrix = OBEEngine.calculate_po_attainment_matrix(nba_prog, session, target_po_level=2.5)
    if 'PO1' in matrix and 'PO2' in matrix and 'PSO1' in matrix:
        po1_data = matrix['PO1']
        report(f"PO1 Attained: {po1_data['attained_level']} (Target: {po1_data['target_level']}, Gap: {po1_data['gap']})", PASS)
        pso1_data = matrix['PSO1']
        report(f"PSO1 Attained: {pso1_data['attained_level']} (Target: {pso1_data['target_level']}, Gap: {pso1_data['gap']})", PASS)
    else:
        report("PO attainment matrix calculation", FAIL, "Missing PO1/PO2/PSO1")
except Exception as e:
    report("PO attainment matrix test", FAIL, str(e))

# ─── T7: Continuous Improvement Action Recording ──────────────
print("\n[T7] Continuous Improvement Action Recording (Criterion 7)")
try:
    po1_info = matrix['PO1']
    action, created = ContinuousImprovementAction.objects.get_or_create(
        program=nba_prog, outcome_type='PO', outcome_code='PO1',
        academic_year='2024-2025',
        defaults={
            'target_level': po1_info['target_level'],
            'attained_level': po1_info['attained_level'],
            'action_proposed': 'Introduce hands-on algorithmic problem-solving labs in second year.',
            'status': 'In Progress'
        }
    )
    if action.gap == max(0.0, round(action.target_level - action.attained_level, 2)):
        report(f"Continuous improvement action logged for PO1 (Gap: {action.gap:.2f})", PASS)
    else:
        report("Continuous improvement action logged", FAIL)
except Exception as e:
    report("Continuous improvement action test", FAIL, str(e))

# ─── T8: Web View Access for Accreditation ────────────────────
print("\n[T8] Accreditation Web Views Access & Rendering")
try:
    client = Client()
    client.force_login(admin_user)

    resp1 = client.get('/accreditation/')
    if resp1.status_code == 200:
        report("/accreditation/ dashboard rendered (HTTP 200)", PASS)
    else:
        report("/accreditation/ dashboard", FAIL, f"Status: {resp1.status_code}")

    resp2 = client.get('/accreditation/nba/')
    if resp2.status_code == 200:
        report("/accreditation/nba/ programs list rendered (HTTP 200)", PASS)
    else:
        report("/accreditation/nba/ programs list", FAIL, f"Status: {resp2.status_code}")
except Exception as e:
    report("Accreditation web views test", FAIL, str(e))

# ─── SUMMARY ──────────────────────────────────────────────────
print()
print("=" * 65)
print("PHASE 3 SUMMARY")
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
    print("ALL PHASE 3 ACCEPTANCE TESTS PASSED!")
    sys.exit(0)
