"""
Outcome-Based Education (OBE) & NBA Attainment Suite (Phase 3)
Calculates Course Outcome (CO) and Program Outcome (PO/PSO) attainments
using configurable, institution-approved assessment methodologies.
"""
from main_app.models import (
    CourseOutcome, COPOMapping, COAttainmentRecord, StudentResult,
    ProgramOutcome, ProgramSpecificOutcome, NBAProgram, Session,
    ContinuousImprovementAction
)


class OBEEngine:
    @staticmethod
    def calculate_co_direct_attainment(
        course_outcome, session=None,
        target_marks_pct=None,
        level_3_students_pct=70.0,
        level_2_students_pct=60.0,
        level_1_students_pct=50.0
    ):
        """
        Calculates direct attainment level (0.0 to 3.0) for a Course Outcome (CO).
        Thresholds and target percentages are explicitly configurable per department/institution policy.
        """
        subject = course_outcome.subject
        results = StudentResult.objects.filter(subject=subject)
        total_students = results.count()
        if total_students == 0:
            return 0.0, 0.0, 0

        # Use CO target_percentage if not explicitly overridden
        target_pct = target_marks_pct or course_outcome.target_percentage or 60.0
        # Assume 100-mark assessment baseline
        target_score = (target_pct / 100.0) * 100.0

        passed_count = results.filter(total__gte=target_score).count()
        actual_students_pct = (passed_count / total_students) * 100.0

        # Multi-tier rubric mapping based on configurable institutional levels
        if actual_students_pct >= level_3_students_pct:
            attainment_level = 3.0
        elif actual_students_pct >= level_2_students_pct:
            attainment_level = 2.0
        elif actual_students_pct >= level_1_students_pct:
            attainment_level = 1.0
        else:
            attainment_level = round(actual_students_pct / level_1_students_pct, 2) if level_1_students_pct > 0 else 0.0

        return attainment_level, actual_students_pct, total_students

    @staticmethod
    def compute_subject_co_attainments(
        subject, session,
        direct_weight=0.80,
        indirect_weight=0.20,
        indirect_attainment_override=None,
        target_attainment_benchmark=2.0
    ):
        """
        Computes direct, indirect, and overall CO attainment for all COs of a subject.
        Direct and indirect weights are fully configurable (must sum to 1.0).
        """
        assert abs((direct_weight + indirect_weight) - 1.0) < 0.001, "Direct and Indirect weights must sum to 1.0"

        cos = subject.course_outcomes.all()
        records = []

        for co in cos:
            direct_level, pct_passed, student_count = OBEEngine.calculate_co_direct_attainment(
                co, session=session,
                target_marks_pct=co.target_percentage,
                level_3_students_pct=co.attainment_target_students_percentage or 70.0
            )

            # Indirect attainment: from surveys or configurable institutional score
            indirect_level = indirect_attainment_override if indirect_attainment_override is not None else 2.5
            overall = round((direct_weight * direct_level) + (indirect_weight * indirect_level), 2)
            target_achieved = overall >= target_attainment_benchmark

            record, _ = COAttainmentRecord.objects.update_or_create(
                subject=subject, session=session, course_outcome=co,
                defaults={
                    'direct_attainment': direct_level,
                    'indirect_attainment': indirect_level,
                    'overall_attainment': overall,
                    'target_achieved': target_achieved,
                }
            )
            records.append({
                'co_code': co.code,
                'direct': direct_level,
                'indirect': indirect_level,
                'overall': overall,
                'target_achieved': target_achieved,
                'student_count': student_count,
                'pct_students_attained': round(pct_passed, 1)
            })

        return records

    @staticmethod
    def calculate_po_attainment_matrix(
        nba_program, session,
        target_po_level=2.5
    ):
        """
        Calculates the Program Outcome (PO1-PO12) and PSO (PSO1-PSO3) attainment matrix
        across all courses in an NBA Program using weighted CO-PO correlation levels.
        """
        pos = nba_program.pos.all().order_by('code')
        psos = nba_program.psos.all().order_by('code')
        
        po_matrix = {}

        for po in list(pos) + list(psos):
            is_pso = isinstance(po, ProgramSpecificOutcome)
            mappings = COPOMapping.objects.filter(pso=po) if is_pso else COPOMapping.objects.filter(po=po)
            mappings = mappings.filter(correlation_level__gt=0)

            total_weighted_attainment = 0.0
            total_correlation = 0.0
            contributing_cos = 0

            for m in mappings:
                # Find attainment record for this CO in the given session
                att_record = COAttainmentRecord.objects.filter(
                    course_outcome=m.course_outcome, session=session
                ).first()

                co_attainment = att_record.overall_attainment if att_record else 2.0
                total_weighted_attainment += co_attainment * m.correlation_level
                total_correlation += m.correlation_level
                contributing_cos += 1

            if total_correlation > 0:
                attained_level = round(total_weighted_attainment / total_correlation, 2)
            else:
                attained_level = 0.0

            gap = max(0.0, round(target_po_level - attained_level, 2))
            target_met = attained_level >= target_po_level

            po_matrix[po.code] = {
                'code': po.code,
                'title': po.title,
                'target_level': target_po_level,
                'attained_level': attained_level,
                'gap': gap,
                'target_met': target_met,
                'contributing_cos': contributing_cos
            }

        return po_matrix

    @staticmethod
    def seed_standard_nba_graduate_attributes(nba_program):
        """
        Seeds the 12 Washington Accord / NBA Graduate Attributes (PO1 to PO12)
        and 2 Program Specific Outcomes (PSOs) for an NBA Program.
        """
        standard_pos = [
            ("PO1", "Engineering Knowledge", "Apply the knowledge of mathematics, science, engineering fundamentals, and an engineering specialization to the solution of complex engineering problems."),
            ("PO2", "Problem Analysis", "Identify, formulate, review research literature, and analyze complex engineering problems reaching substantiated conclusions."),
            ("PO3", "Design/Development of Solutions", "Design solutions for complex engineering problems and design system components or processes that meet the specified needs."),
            ("PO4", "Conduct Investigations of Complex Problems", "Use research-based knowledge and research methods including design of experiments, analysis and interpretation of data."),
            ("PO5", "Modern Tool Usage", "Create, select, and apply appropriate techniques, resources, and modern engineering and IT tools."),
            ("PO6", "The Engineer and Society", "Apply reasoning informed by the contextual knowledge to assess societal, health, safety, legal and cultural issues."),
            ("PO7", "Environment and Sustainability", "Understand the impact of the professional engineering solutions in societal and environmental contexts."),
            ("PO8", "Ethics", "Apply ethical principles and commit to professional ethics and responsibilities and norms of the engineering practice."),
            ("PO9", "Individual and Team Work", "Function effectively as an individual, and as a member or leader in diverse teams, and in multidisciplinary settings."),
            ("PO10", "Communication", "Communicate effectively on complex engineering activities with the engineering community and with society at large."),
            ("PO11", "Project Management and Finance", "Demonstrate knowledge and understanding of the engineering and management principles and apply these to one's own work."),
            ("PO12", "Life-long Learning", "Recognize the need for, and have the preparation and ability to engage in independent and life-long learning in the broadest context of technological change."),
        ]

        created_pos = []
        for code, title, desc in standard_pos:
            po, _ = ProgramOutcome.objects.get_or_create(
                program=nba_program, code=code,
                defaults={'title': title, 'description': desc}
            )
            created_pos.append(po)

        # Standard PSOs
        psos = [
            ("PSO1", "Professional Core Proficiency", "Design, develop, and maintain software and hardware solutions tailored to modern industrial requirements."),
            ("PSO2", "Innovation and Specialized Systems", "Apply modern techniques in artificial intelligence, cloud systems, and cybersecurity to solve real-world problems.")
        ]
        created_psos = []
        for code, title, desc in psos:
            pso, _ = ProgramSpecificOutcome.objects.get_or_create(
                program=nba_program, code=code,
                defaults={'title': title, 'description': desc}
            )
            created_psos.append(pso)

        return created_pos, created_psos
