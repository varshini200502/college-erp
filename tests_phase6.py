"""
Phase 6 Acceptance Test Suite: NBA Criteria Automation & SAR Export Engine
"""
import sys, os, json, csv, io
sys.path.insert(0, r'D:\College_ERP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django
django.setup()

from django.test import Client
from main_app.models import (
    CustomUser, Course, NBAProgram, NAACCriterion, NAACMetricData,
    ProgramOutcome, ProgramSpecificOutcome, ProgramEducationalObjective,
    Staff, Student, Subject
)
from main_app.naac_automation import sync_all_naac_criteria, sync_criterion
from main_app.sar_export import SARExportEngine
from main_app.accreditation_views import seed_naac_criteria_if_needed, seed_standard_nba_pos

PASS = "PASS"
FAIL = "FAIL"
results = []

def report(name, status, detail=""):
    results.append((name, status, detail))
    icon = "✓" if status == PASS else "✗"
    print(f"  [{icon}] {name}: {status}" + (f" — {detail}" if detail else ""))

print("=" * 65)
print("PHASE 6 ACCEPTANCE TEST SUITE")
print("=" * 65)

# Seed criteria and NBA program for testing
seed_naac_criteria_if_needed()
course_cse = Course.objects.filter(name__icontains="Computer").first() or Course.objects.first()
nba_prog, _ = NBAProgram.objects.get_or_create(
    course=course_cse,
    defaults={'program_name': f"B.Tech in {course_cse.name}", 'tier': 'Tier I'}
)
if nba_prog.pos.count() == 0:
    seed_standard_nba_pos(nba_prog)

admin_user = CustomUser.objects.filter(user_type=1).first()

# ─── T1: NAAC Full Institutional Auto-Sync ───────────────────────
print("\n[T1] NAAC Full Institutional Auto-Sync across 7 Criteria")
try:
    sync_summary = sync_all_naac_criteria(academic_year="2024-2025")
    all_positive = all(count >= 0 for count in sync_summary.values())
    has_7_crit = len(sync_summary) == 7
    if all_positive and has_7_crit:
        report(f"Auto-synced all 7 NAAC criteria ({len(sync_summary)} criteria, total metrics updated)", PASS)
    else:
        report("NAAC full sync", FAIL, f"Summary: {sync_summary}")
except Exception as e:
    report("NAAC full sync test", FAIL, str(e))

# ─── T2: NAAC Live Metric Data Verification ───────────────────────
print("\n[T2] NAAC Live Metric Data Integrity (Criterion 2 & 3)")
try:
    c2 = NAACCriterion.objects.get(criterion_number=2)
    m_sfr = NAACMetricData.objects.filter(criterion=c2, metric_code="2.2.2").first()
    c3 = NAACCriterion.objects.get(criterion_number=3)
    m_pubs = NAACMetricData.objects.filter(criterion=c3, metric_code="3.3.1").first()

    if m_sfr and m_sfr.quantitative_value > 0 and m_pubs is not None:
        report(f"Live metrics populated: SFR={m_sfr.quantitative_value}:1, Pubs count={m_pubs.quantitative_value}", PASS)
    else:
        report("Live metric verification", FAIL, f"SFR metric={m_sfr}, Pubs metric={m_pubs}")
except Exception as e:
    report("Live metric verification test", FAIL, str(e))

# ─── T3: NBA Multi-Criteria SAR Dictionary Generation ─────────────
print("\n[T3] NBA Multi-Criteria SAR Dictionary Generation")
try:
    sar_dict = SARExportEngine.generate_nba_sar(nba_prog, academic_year="2024-2025")
    required_sections = ["criterion_1", "criterion_2", "criterion_3", "criterion_4", "criterion_5", "criterion_7", "criterion_9", "criterion_10"]
    missing = [sec for sec in required_sections if sec not in sar_dict]
    if not missing:
        report(f"SAR multi-criteria data generated ({len(sar_dict)} top-level sections, Tier={sar_dict['tier']})", PASS)
    else:
        report("SAR generation", FAIL, f"Missing sections: {missing}")
except Exception as e:
    report("SAR generation test", FAIL, str(e))

# ─── T4: SAR JSON Serialization & Schema Validation ──────────────
print("\n[T4] SAR JSON Serialization & Schema Validation")
try:
    json_str = SARExportEngine.export_sar_json(nba_prog, academic_year="2024-2025")
    parsed = json.loads(json_str)
    if parsed.get("program_name") == nba_prog.program_name and "criterion_4" in parsed:
        report(f"SAR serialized to valid JSON ({len(json_str)} bytes)", PASS)
    else:
        report("SAR JSON export", FAIL, "Parsed JSON missing program_name or criterion_4")
except Exception as e:
    report("SAR JSON export test", FAIL, str(e))

# ─── T5: SAR Tabular CSV Export Formatting ────────────────────────
print("\n[T5] SAR Tabular CSV Export Formatting")
try:
    csv_str = SARExportEngine.export_sar_csv(nba_prog, academic_year="2024-2025")
    reader = csv.reader(io.StringIO(csv_str))
    rows = list(reader)
    has_header = any("NBA SELF ASSESSMENT REPORT" in str(r) for r in rows[:3])
    has_crit4 = any("Crit 4" in str(r) for r in rows)
    has_crit5 = any("Crit 5" in str(r) for r in rows)
    if has_header and has_crit4 and has_crit5:
        report(f"SAR flattened to tabular CSV ({len(rows)} rows with criteria breakdown)", PASS)
    else:
        report("SAR CSV export", FAIL, f"Rows: {len(rows)}, Header: {has_header}, Crit4: {has_crit4}, Crit5: {has_crit5}")
except Exception as e:
    report("SAR CSV export test", FAIL, str(e))

# ─── T6: SAR Export Web Endpoint (JSON format) ───────────────────
print("\n[T6] SAR Export Web Endpoint Access (JSON)")
try:
    client = Client()
    client.force_login(admin_user)
    resp = client.get(f'/accreditation/nba/sar/{nba_prog.id}/?format=json')
    if resp.status_code == 200 and 'application/json' in resp['Content-Type']:
        payload = json.loads(resp.content.decode('utf-8'))
        if payload.get("program_id") == nba_prog.id:
            report(f"GET /accreditation/nba/sar/{nba_prog.id}/?format=json returned HTTP 200 JSON", PASS)
        else:
            report("SAR web endpoint JSON content", FAIL, f"Payload mismatch: {payload.keys()}")
    else:
        report("SAR web endpoint JSON", FAIL, f"Status: {resp.status_code}, Type: {resp.get('Content-Type')}")
except Exception as e:
    report("SAR web endpoint JSON test", FAIL, str(e))

# ─── T7: SAR Export Web Endpoint (CSV format) ────────────────────
print("\n[T7] SAR Export Web Endpoint Access (CSV)")
try:
    client = Client()
    client.force_login(admin_user)
    resp = client.get(f'/accreditation/nba/sar/{nba_prog.id}/?format=csv')
    if resp.status_code == 200 and 'text/csv' in resp['Content-Type']:
        content_disp = resp.get('Content-Disposition', '')
        if 'attachment' in content_disp and '.csv' in content_disp:
            report(f"GET /accreditation/nba/sar/{nba_prog.id}/?format=csv returned HTTP 200 CSV Attachment", PASS)
        else:
            report("SAR web endpoint CSV header", FAIL, f"Content-Disposition: {content_disp}")
    else:
        report("SAR web endpoint CSV", FAIL, f"Status: {resp.status_code}, Type: {resp.get('Content-Type')}")
except Exception as e:
    report("SAR web endpoint CSV test", FAIL, str(e))

# ─── T8: Verified Non-Assumption of NBA Hardcoded Thresholds ─────
print("\n[T8] Integrity Check: No Hardcoded NBA Pass/Fail Verdicts in SAR Export")
try:
    sar = SARExportEngine.generate_nba_sar(nba_prog)
    # Ensure SAR provides raw quantitative figures rather than fabricated pass/fail accreditation decisions
    has_verdict = "accreditation_status" in sar or "decision" in sar
    if not has_verdict:
        report("SAR strictly outputs verified metrics without unapproved accreditation decisions: PASS", PASS)
    else:
        report("NBA non-assumption check", FAIL, "Found speculative accreditation decision in SAR export")
except Exception as e:
    report("NBA non-assumption check test", FAIL, str(e))

# ─── SUMMARY ──────────────────────────────────────────────────
print()
print("=" * 65)
print("PHASE 6 SUMMARY")
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
    print("ALL PHASE 6 ACCEPTANCE TESTS PASSED!")
    sys.exit(0)
