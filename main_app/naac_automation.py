"""
NAAC Automation Service — Phase 6
Syncs live ERP data into NAACMetricData for all 7 NAAC criteria.
No hardcoded thresholds. No benchmark decisions. Data-only sync.
"""
import logging
from datetime import date

from django.db.models import Sum, Count, Avg

logger = logging.getLogger(__name__)


def sync_all_naac_criteria(academic_year: str = None) -> dict:
    """
    Synchronise all 7 NAAC criteria from live ERP records.
    Returns a summary dict: {criterion_number: metrics_updated_count}.
    """
    # Avoid circular imports — import inside function
    from .models import (
        NAACCriterion, Student, Staff, Course, Subject,
        FacultyPublication, FacultyTraining, FacultyPatent,
        StudentPlacement, StudentAchievement,
        FeePayment, CollegeExpense, DepartmentBudget,
        LeaveReportStaff,
    )

    if academic_year is None:
        academic_year = _current_academic_year()

    summary = {}
    criteria = NAACCriterion.objects.all().order_by("criterion_number")

    for criterion in criteria:
        n = criterion.criterion_number
        try:
            count = sync_criterion(criterion, academic_year)
            summary[n] = count
            logger.info("NAAC Criterion %d synced: %d metric(s) updated.", n, count)
        except Exception as exc:  # noqa: BLE001
            logger.error("NAAC Criterion %d sync failed: %s", n, exc)
            summary[n] = -1  # -1 signals error

    return summary


def _current_academic_year() -> str:
    """Return best-guess current academic year (e.g. '2024-2025')."""
    today = date.today()
    start = today.year if today.month >= 6 else today.year - 1
    return f"{start}-{start + 1}"


def _upsert(criterion, metric_code, title, value, notes, academic_year):
    """Create or update a single NAACMetricData row."""
    from .models import NAACMetricData
    obj, created = NAACMetricData.objects.update_or_create(
        criterion=criterion,
        metric_code=metric_code,
        academic_year=academic_year,
        defaults={
            "title": title,
            "quantitative_value": float(value),
            "qualitative_notes": notes,
        },
    )
    return obj, created


def sync_criterion(criterion, academic_year: str = None) -> int:
    """Dispatch to per-criterion sync helper. Returns count of rows written."""
    if academic_year is None:
        academic_year = _current_academic_year()
    from .models import (
        Student, Staff, Course, Subject,
        FacultyPublication, FacultyPatent, FacultyTraining,
        StudentPlacement, StudentAchievement,
        FeePayment, CollegeExpense,
        LeaveReportStaff,
    )
    n = criterion.criterion_number
    written = 0

    # ── Criterion 1: Curricular Aspects ───────────────────────────────────────
    if n == 1:
        total_programmes = Course.objects.count()
        total_subjects = Subject.objects.count()
        _, _ = _upsert(
            criterion, "1.1.1",
            "Curricula Developed and Implemented",
            total_programmes,
            f"Programmes: {total_programmes} | Subjects offered: {total_subjects}",
            academic_year,
        )
        written += 1

    # ── Criterion 2: Teaching-Learning & Evaluation ───────────────────────────
    elif n == 2:
        total_students = Student.objects.filter(status="Active").count()
        total_faculty = Staff.objects.filter(employment_status="Active").count()
        sfr = round(total_students / total_faculty, 2) if total_faculty else 0

        _upsert(
            criterion, "2.2.2",
            "Student : Full-Time Teacher Ratio",
            sfr,
            f"Active Students: {total_students} | Active Faculty: {total_faculty} | Ratio: {sfr}:1",
            academic_year,
        )
        written += 1

        # PhD faculty percentage (data point only — no threshold applied)
        phd_count = Staff.objects.filter(
            employment_status="Active",
            highest_qualification__icontains="Ph.D"
        ).count()
        phd_pct = round(phd_count / total_faculty * 100, 1) if total_faculty else 0
        _upsert(
            criterion, "2.4.2",
            "Full-Time Teachers with Ph.D Qualification",
            phd_pct,
            f"Ph.D holders: {phd_count} / {total_faculty} active faculty = {phd_pct}%",
            academic_year,
        )
        written += 1

    # ── Criterion 3: Research, Innovations & Extension ───────────────────────
    elif n == 3:
        scopus_wos = FacultyPublication.objects.filter(
            indexing__in=["Scopus", "Web of Science"]
        ).count()
        total_pubs = FacultyPublication.objects.count()
        _upsert(
            criterion, "3.3.1",
            "Number of Research Papers Published (Scopus / WoS)",
            scopus_wos,
            f"Total publications: {total_pubs} | Scopus/WoS indexed: {scopus_wos}",
            academic_year,
        )
        written += 1

        granted_patents = FacultyPatent.objects.filter(status="Granted").count()
        total_patents = FacultyPatent.objects.count()
        _upsert(
            criterion, "3.4.3",
            "Number of Patents Granted",
            granted_patents,
            f"Total patents filed: {total_patents} | Granted: {granted_patents}",
            academic_year,
        )
        written += 1

        fdp_count = FacultyTraining.objects.filter(
            training_type__in=["FDP", "STTP", "Workshop"]
        ).count()
        _upsert(
            criterion, "3.7.1",
            "Number of Collaborative Activities (FDP/STTP/Workshop)",
            fdp_count,
            f"Faculty development and training events: {fdp_count}",
            academic_year,
        )
        written += 1

    # ── Criterion 4: Infrastructure & Learning Resources ─────────────────────
    elif n == 4:
        # Structural/physical data not in ERP — emit zero as placeholder
        _upsert(
            criterion, "4.1.1",
            "Physical Facilities (Classrooms / Labs) — Manual Entry Required",
            0,
            "Physical infrastructure data must be entered manually. ERP does not manage room inventory.",
            academic_year,
        )
        written += 1

    # ── Criterion 5: Student Support & Progression ───────────────────────────
    elif n == 5:
        placed = StudentPlacement.objects.count()
        _upsert(
            criterion, "5.2.1",
            "Placement and Higher Education of Outgoing Students",
            placed,
            f"Total student placement / higher education records: {placed}",
            academic_year,
        )
        written += 1

        achievements = StudentAchievement.objects.count()
        _upsert(
            criterion, "5.3.1",
            "Awards / Medals / Distinctions Won by Students",
            achievements,
            f"Student achievement records: {achievements}",
            academic_year,
        )
        written += 1

    # ── Criterion 6: Governance, Leadership & Management ─────────────────────
    elif n == 6:
        # Faculty retention: proxy = active / (active + resigned) — no HR module yet
        active_faculty = Staff.objects.filter(employment_status="Active").count()
        _upsert(
            criterion, "6.2.2",
            "Implementation of e-Governance",
            1,
            f"ERP operational with {active_faculty} active faculty users. e-Gov modules: student, finance, attendance, marks, accreditation.",
            academic_year,
        )
        written += 1

    # ── Criterion 7: Institutional Values & Best Practices ───────────────────
    elif n == 7:
        _upsert(
            criterion, "7.1.1",
            "Measures for Gender Equity — Manual Entry Required",
            0,
            "Gender equity and institutional value data must be entered manually by the IQAC coordinator.",
            academic_year,
        )
        written += 1

    return written
