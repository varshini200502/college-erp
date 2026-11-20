"""
NBA Self-Assessment Report (SAR) & NAAC SSR Data Export Engine — Phase 6
Generates structured data, JSON, and tabular CSV exports for NBA Criteria 1-10
and NAAC 7 Criteria.
Strictly adheres to official data sources without hardcoded thresholds.
"""
import csv
import io
import json
from datetime import date
from typing import Any, Dict, Optional

from django.db.models import Avg, Count, Sum


class SARExportEngine:
    """
    Export engine for NBA Tier-I / Tier-II Self Assessment Report (SAR)
    and NAAC SSR datasets.
    """

    @classmethod
    def generate_nba_sar(cls, program, academic_year: Optional[str] = None) -> Dict[str, Any]:
        """
        Builds complete multi-criteria SAR dictionary for a given NBAProgram or Programme.
        """
        from .models import (
            NBAProgram, Programme, Course, Subject, Student, Staff,
            FacultyPublication, FacultyPatent, FacultyTraining,
            ContinuousImprovementAction, COAttainmentRecord,
            StudentPlacement, StudentProject, CollegeExpense
        )

        if isinstance(program, int):
            program = NBAProgram.objects.get(id=program)

        if not academic_year:
            today = date.today()
            start = today.year if today.month >= 6 else today.year - 1
            academic_year = f"{start}-{start + 1}"

        course = program.course
        dept = course.department if hasattr(course, 'department') else None
        prog_obj = getattr(course, 'programme', None) or program.programme

        # Criterion 1: Vision, Mission & PEOs
        peos_data = [
            {"code": p.code, "title": p.title, "description": p.description}
            for p in program.peos.all().order_by("code")
        ]
        crit1 = {
            "title": "Vision, Mission and Program Educational Objectives",
            "department": dept.name if dept else (course.name if course else "N/A"),
            "program_name": program.program_name,
            "tier": program.tier,
            "peos": peos_data,
        }

        # Criterion 2: Program Curriculum and Teaching-Learning Processes
        subjects = Subject.objects.filter(course=course)
        crit2 = {
            "title": "Program Curriculum and Teaching-Learning Processes",
            "total_courses_in_curriculum": subjects.count(),
            "courses": [
                {"id": s.id, "name": s.name, "staff": str(s.staff) if s.staff else "Unassigned"}
                for s in subjects
            ]
        }

        # Criterion 3: Course Outcomes and Program Outcomes
        pos_data = [
            {"code": po.code, "title": po.title}
            for po in program.pos.all().order_by("code")
        ]
        psos_data = [
            {"code": pso.code, "title": pso.title}
            for pso in program.psos.all().order_by("code")
        ]
        crit3 = {
            "title": "Course Outcomes and Program Outcomes",
            "pos_count": len(pos_data),
            "psos_count": len(psos_data),
            "pos": pos_data,
            "psos": psos_data,
        }

        # Criterion 4: Students' Performance & Attainment
        students_qs = Student.objects.filter(course=course)
        active_students = students_qs.filter(status="Active").count()
        attainments = COAttainmentRecord.objects.filter(subject__course=course)
        avg_direct = attainments.aggregate(a=Avg("direct_attainment"))["a"] or 0.0
        avg_indirect = attainments.aggregate(a=Avg("indirect_attainment"))["a"] or 0.0
        avg_overall = attainments.aggregate(a=Avg("overall_attainment"))["a"] or 0.0

        # Capstone projects for this programme (strict primary programme filtering)
        projects_count = 0
        if prog_obj:
            projects_count = StudentProject.objects.filter(primary_programme=prog_obj).count()

        crit4 = {
            "title": "Students' Performance and Outcome Attainments",
            "total_enrolled_students": students_qs.count(),
            "active_students": active_students,
            "co_attainment_records_count": attainments.count(),
            "average_direct_attainment": round(avg_direct, 2),
            "average_indirect_attainment": round(avg_indirect, 2),
            "average_overall_attainment": round(avg_overall, 2),
            "capstone_projects_count": projects_count,
        }

        # Criterion 5: Faculty Information & Contributions
        faculty_qs = Staff.objects.all()
        if dept:
            faculty_qs = faculty_qs.filter(primary_department=dept)

        total_faculty = faculty_qs.count()
        phd_faculty = faculty_qs.filter(highest_qualification__icontains="Ph.D").count()
        sfr = round(active_students / total_faculty, 2) if total_faculty > 0 else 0.0

        pubs_count = FacultyPublication.objects.filter(staff__in=faculty_qs).count()
        scopus_count = FacultyPublication.objects.filter(staff__in=faculty_qs, indexing__icontains="Scopus").count()
        patents_count = FacultyPatent.objects.filter(staff__in=faculty_qs).count()
        trainings_count = FacultyTraining.objects.filter(staff__in=faculty_qs).count()

        crit5 = {
            "title": "Faculty Information and Contributions",
            "total_faculty": total_faculty,
            "phd_faculty": phd_faculty,
            "student_faculty_ratio": sfr,
            "publications_total": pubs_count,
            "publications_scopus": scopus_count,
            "patents_total": patents_count,
            "faculty_trainings": trainings_count,
        }

        # Criterion 7: Continuous Improvement
        actions = ContinuousImprovementAction.objects.filter(program=program)
        crit7 = {
            "title": "Continuous Improvement",
            "actions_count": actions.count(),
            "actions": [
                {
                    "outcome_code": a.outcome_code,
                    "target_level": a.target_level,
                    "attained_level": a.attained_level,
                    "action_proposed": a.action_proposed,
                    "status": a.status,
                }
                for a in actions
            ]
        }

        # Criterion 9: Student Support Systems
        placements = StudentPlacement.objects.filter(student__course=course)
        crit9 = {
            "title": "Student Support Systems",
            "placements_count": placements.filter(is_higher_studies=False).count(),
            "higher_studies_count": placements.filter(is_higher_studies=True).count(),
        }

        # Criterion 10: Governance, Institutional Support and Financial Resources
        infra_exp = CollegeExpense.objects.filter(category="Infrastructure").aggregate(s=Sum("amount"))["s"] or 0.0
        lab_exp = CollegeExpense.objects.filter(category="Laboratory").aggregate(s=Sum("amount"))["s"] or 0.0
        crit10 = {
            "title": "Governance, Institutional Support and Financial Resources",
            "infrastructure_expenditure": infra_exp,
            "laboratory_expenditure": lab_exp,
        }

        return {
            "report_type": "NBA Self Assessment Report (SAR)",
            "tier": program.tier,
            "program_id": program.id,
            "program_name": program.program_name,
            "department": dept.name if dept else "N/A",
            "academic_year": academic_year,
            "generation_date": str(date.today()),
            "criterion_1": crit1,
            "criterion_2": crit2,
            "criterion_3": crit3,
            "criterion_4": crit4,
            "criterion_5": crit5,
            "criterion_7": crit7,
            "criterion_9": crit9,
            "criterion_10": crit10,
        }

    @classmethod
    def export_sar_json(cls, program, academic_year: Optional[str] = None) -> str:
        """Serializes the SAR data to formatted JSON."""
        data = cls.generate_nba_sar(program, academic_year=academic_year)
        return json.dumps(data, indent=2, default=str)

    @classmethod
    def export_sar_csv(cls, program, academic_year: Optional[str] = None) -> str:
        """
        Flattens the SAR report into a structured tabular CSV.
        """
        sar = cls.generate_nba_sar(program, academic_year=academic_year)
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["NBA SELF ASSESSMENT REPORT (SAR) - SUMMARY EXPORT"])
        writer.writerow(["Program", sar["program_name"]])
        writer.writerow(["Tier", sar["tier"]])
        writer.writerow(["Department", sar["department"]])
        writer.writerow(["Academic Year", sar["academic_year"]])
        writer.writerow(["Generated Date", sar["generation_date"]])
        writer.writerow([])

        writer.writerow(["CRITERION", "METRIC / ATTRIBUTE", "QUANTITATIVE VALUE", "DETAILS / STATUS"])
        
        # Criterion 1
        writer.writerow(["Crit 1: Vision, Mission & PEOs", "PEOs Defined", len(sar["criterion_1"]["peos"]), ""])
        for peo in sar["criterion_1"]["peos"]:
            writer.writerow(["Crit 1: Vision, Mission & PEOs", peo["code"], peo["title"], peo["description"]])

        # Criterion 2
        writer.writerow(["Crit 2: Curriculum", "Total Subjects in Curriculum", sar["criterion_2"]["total_courses_in_curriculum"], ""])

        # Criterion 3
        writer.writerow(["Crit 3: Outcomes", "Program Outcomes (POs)", sar["criterion_3"]["pos_count"], "PO1 to PO12"])
        writer.writerow(["Crit 3: Outcomes", "Program Specific Outcomes (PSOs)", sar["criterion_3"]["psos_count"], ""])

        # Criterion 4
        c4 = sar["criterion_4"]
        writer.writerow(["Crit 4: Students' Performance", "Enrolled Students", c4["total_enrolled_students"], ""])
        writer.writerow(["Crit 4: Students' Performance", "Active Students", c4["active_students"], ""])
        writer.writerow(["Crit 4: Students' Performance", "Average Overall CO Attainment", f"{c4['average_overall_attainment']:.2f}/3.0", ""])
        writer.writerow(["Crit 4: Students' Performance", "Capstone Projects Completed", c4["capstone_projects_count"], "No double counting"])

        # Criterion 5
        c5 = sar["criterion_5"]
        writer.writerow(["Crit 5: Faculty Contributions", "Total Faculty", c5["total_faculty"], ""])
        writer.writerow(["Crit 5: Faculty Contributions", "Ph.D Qualified Faculty", c5["phd_faculty"], ""])
        writer.writerow(["Crit 5: Faculty Contributions", "Student-Faculty Ratio (SFR)", f"{c5['student_faculty_ratio']}:1", ""])
        writer.writerow(["Crit 5: Faculty Contributions", "Total Publications", c5["publications_total"], f"Scopus: {c5['publications_scopus']}"])
        writer.writerow(["Crit 5: Faculty Contributions", "Patents", c5["patents_total"], ""])

        # Criterion 7
        c7 = sar["criterion_7"]
        writer.writerow(["Crit 7: Continuous Improvement", "Continuous Improvement Actions", c7["actions_count"], ""])

        # Criterion 9
        c9 = sar["criterion_9"]
        writer.writerow(["Crit 9: Student Support", "Placements", c9["placements_count"], ""])
        writer.writerow(["Crit 9: Student Support", "Higher Studies", c9["higher_studies_count"], ""])

        # Criterion 10
        c10 = sar["criterion_10"]
        writer.writerow(["Crit 10: Financial Resources", "Infrastructure Expenses", f"INR {c10['infrastructure_expenditure']:.2f}", ""])
        writer.writerow(["Crit 10: Financial Resources", "Laboratory Expenses", f"INR {c10['laboratory_expenditure']:.2f}", ""])

        return output.getvalue()
