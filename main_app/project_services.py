"""
Capstone Projects & Faculty Research Portfolio Services (Phase 5)
Provides project lifecycle management with rubric scoring, interdisciplinary
handling without NBA double-counting, and faculty academic portfolios.
"""
from django.db import transaction
from django.db.models import Sum, Count, Avg
from .models import (
    StudentProject, Staff, Student, Programme,
    FacultyPublication, FacultyPatent, FacultyTraining
)


class ProjectService:
    @staticmethod
    def create_project(
        title, project_type, academic_year, primary_programme,
        guide, student_ids, secondary_programme=None, co_guide=None,
        abstract=""
    ):
        """
        Creates a capstone/mini project with strict primary department ownership.
        Even for interdisciplinary projects with a co-guide from another department,
        ownership is explicitly anchored to primary_programme to prevent NBA double-counting.
        """
        with transaction.atomic():
            project = StudentProject.objects.create(
                title=title,
                project_type=project_type,
                academic_year=academic_year,
                primary_programme=primary_programme,
                secondary_programme=secondary_programme,
                guide=guide,
                co_guide=co_guide,
                abstract=abstract,
                is_nba_credited=True  # Credited ONLY to primary_programme
            )
            for sid in student_ids:
                try:
                    s = Student.objects.get(id=sid)
                    project.students.add(s)
                except Student.DoesNotExist:
                    pass
            return project

    @staticmethod
    def record_rubric_evaluation(project, review1_score, review2_score, final_score):
        """
        Records rubric scores across review milestones and automatically recalculates total score.
        """
        project.rubric_score_review1 = float(review1_score or 0.0)
        project.rubric_score_review2 = float(review2_score or 0.0)
        project.rubric_score_final = float(final_score or 0.0)
        project.save()  # Triggers save() total calculation
        return project.total_score

    @staticmethod
    def get_programme_nba_projects(programme, academic_year=None):
        """
        Retrieves projects eligible for NBA SAR Criterion 4/Criterion 5 reporting for a programme.
        Ensures projects with secondary programme affiliations are counted exactly ONCE under primary programme.
        """
        qs = StudentProject.objects.filter(primary_programme=programme, is_nba_credited=True)
        if academic_year:
            qs = qs.filter(academic_year=academic_year)
        return qs

    @staticmethod
    def get_faculty_research_portfolio(staff):
        """
        Aggregates the complete scholarly portfolio for a faculty member:
        Publications, Patents, FDPs / Trainings, and Guided Student Projects.
        """
        pubs = FacultyPublication.objects.filter(staff=staff).order_by('-publication_date')
        patents = FacultyPatent.objects.filter(staff=staff).order_by('-created_at')
        trainings = FacultyTraining.objects.filter(staff=staff).order_by('-start_date')
        guided_projects = StudentProject.objects.filter(guide=staff).order_by('-created_at')
        co_guided_projects = StudentProject.objects.filter(co_guide=staff).order_by('-created_at')

        scopus_count = pubs.filter(indexing__icontains='Scopus').count()
        wos_count = pubs.filter(indexing__icontains='Web of Science').count()
        granted_patents = patents.filter(status='Granted').count()

        return {
            'staff': staff,
            'total_publications': pubs.count(),
            'scopus_count': scopus_count,
            'wos_count': wos_count,
            'publications': pubs,
            'total_patents': patents.count(),
            'granted_patents': granted_patents,
            'patents': patents,
            'total_trainings': trainings.count(),
            'trainings': trainings,
            'guided_projects_count': guided_projects.count(),
            'guided_projects': guided_projects,
            'co_guided_projects_count': co_guided_projects.count(),
        }
