"""
Academic Lifecycle, Regulations & OBE Evaluation Engine (Phase 2)
Handles semester progression, detention, condonation, credit validation,
and graduation / alumni transitions according to officially approved regulations.
"""
from django.db import transaction
from django.utils import timezone
from .models import (
    Student, AcademicRegulation, StudentAcademicHistory, AlumniProfile,
    Programme, CustomUser
)


class AcademicEngine:
    @staticmethod
    def get_applicable_regulation(programme, year=None, require_approved=False):
        """
        Retrieves the active academic regulation for a programme.
        Prioritizes officially Approved regulations over Provisional ones.
        """
        if not programme:
            return None
        qs = AcademicRegulation.objects.filter(programme=programme, is_active=True)
        if year:
            qs = qs.filter(effective_year__lte=year)
        
        approved = qs.filter(approval_status='Approved').order_by('-effective_year').first()
        if approved:
            return approved
        if require_approved:
            return None
        return qs.order_by('-effective_year').first()

    @staticmethod
    def evaluate_semester_progression(
        student, semester, academic_year, credits_registered, credits_earned,
        sgpa, attendance_pct, fee_cleared=False, library_cleared=False,
        evaluated_by=None, medical_certificate=False
    ):
        """
        Evaluates semester progression strictly based on approved institutional regulations.
        If regulation is unset, provisional, or unapproved, flags as 'Pending' without
        applying arbitrary hardcoded thresholds.
        """
        prog = student.programme
        reg = AcademicEngine.get_applicable_regulation(prog, student.batch.admission_year if student.batch else None)

        history, _ = StudentAcademicHistory.objects.get_or_create(
            student=student, semester=semester, academic_year=academic_year,
            defaults={
                'credits_registered': credits_registered,
                'credits_earned': credits_earned,
                'sgpa': sgpa,
                'attendance_percentage': attendance_pct,
                'fee_cleared': fee_cleared,
                'library_cleared': library_cleared,
                'verified_by': evaluated_by
            }
        )
        history.credits_registered = credits_registered
        history.credits_earned = credits_earned
        history.sgpa = sgpa
        history.attendance_percentage = attendance_pct
        history.fee_cleared = fee_cleared
        history.library_cleared = library_cleared
        history.verified_by = evaluated_by

        # RULE: Unapproved / Provisional policies CANNOT automatically detain or promote
        if not reg or reg.approval_status != 'Approved':
            history.promotion_status = 'Pending'
            history.remarks = (
                "Evaluation Pending: No verified & approved academic regulation on file for this programme. "
                "Automatic academic decisions are withheld until officially approved regulations are registered."
            )
            history.save()
            return {
                'status': 'Pending',
                'decision': 'Withheld',
                'reason': 'Academic regulation unapproved or missing',
                'history_id': history.id
            }

        # Approved regulation checks
        decision = 'Promoted'
        reason = f"Passed Semester {semester} with SGPA {sgpa:.2f}"

        # 1. Attendance Check
        if reg.min_attendance_percentage is not None:
            if attendance_pct < reg.min_attendance_percentage:
                if (
                    reg.condonation_min_percentage is not None
                    and attendance_pct >= reg.condonation_min_percentage
                    and medical_certificate
                ):
                    decision = 'Condoned'
                    fee_note = f" (Condonation Fee: Rs. {reg.condonation_fee:.2f})" if reg.condonation_fee else ""
                    reason = f"Attendance condoned at {attendance_pct:.1f}% on medical grounds{fee_note}."
                else:
                    decision = 'Detained_Attendance'
                    reason = f"Detained: Attendance {attendance_pct:.1f}% below required {reg.min_attendance_percentage:.1f}%."

        # 2. Credit Check (only if not already detained by attendance)
        if decision != 'Detained_Attendance' and reg.min_credits_for_promotion is not None:
            # Check cumulative credits earned up to this semester
            past_credits = sum(
                h.credits_earned for h in student.academic_history.exclude(id=history.id)
            ) + credits_earned
            if past_credits < reg.min_credits_for_promotion:
                decision = 'Detained_Credits'
                reason = f"Detained: Cumulative credits {past_credits:.1f} below minimum required {reg.min_credits_for_promotion}."

        history.promotion_status = decision
        history.remarks = reason
        history.save()

        # Update student's SGPA / CGPA
        all_histories = student.academic_history.filter(credits_registered__gt=0)
        total_cred = sum(h.credits_registered for h in all_histories)
        if total_cred > 0:
            cgpa = sum(h.sgpa * h.credits_registered for h in all_histories) / total_cred
            student.cgpa = round(cgpa, 2)
        student.sgpa = round(sgpa, 2)
        if decision in ['Promoted', 'Condoned'] and student.current_semester == semester:
            student.current_semester = min(student.current_semester + 1, prog.total_semesters if prog else 8)
        student.save()

        return {
            'status': decision,
            'decision': decision,
            'reason': reason,
            'cgpa': student.cgpa,
            'history_id': history.id
        }

    @staticmethod
    def evaluate_graduation(student, verified_by=None):
        """
        Evaluates whether a student has completed all degree requirements for graduation.
        Transitions student to 'Graduated' and creates AlumniProfile if all checks pass.
        """
        prog = student.programme
        if not prog:
            return {'success': False, 'reason': 'Student has no assigned academic programme'}

        reg = AcademicEngine.get_applicable_regulation(prog, student.batch.admission_year if student.batch else None)
        if not reg or reg.approval_status != 'Approved':
            return {
                'success': False,
                'reason': 'Graduation withheld: Approved academic regulations are required for degree audit.'
            }

        histories = student.academic_history.all()
        completed_semesters = histories.filter(promotion_status__in=['Promoted', 'Passed', 'Condoned']).count()

        if completed_semesters < prog.total_semesters:
            return {
                'success': False,
                'reason': f"Incomplete semesters: {completed_semesters} of {prog.total_semesters} semesters passed."
            }

        # Check CGPA requirement
        if reg.min_cgpa_for_award is not None and student.cgpa < reg.min_cgpa_for_award:
            return {
                'success': False,
                'reason': f"CGPA {student.cgpa:.2f} below required {reg.min_cgpa_for_award:.2f} for degree award."
            }

        # Check fee clearance
        uncleared_fees = histories.filter(fee_cleared=False).exists()
        if uncleared_fees:
            return {'success': False, 'reason': "Institutional fee dues exist. Fee clearance required."}

        # Check library clearance
        uncleared_library = histories.filter(library_cleared=False).exists()
        if uncleared_library:
            return {'success': False, 'reason': "Library dues exist. Library clearance required."}

        # Graduation Approved
        with transaction.atomic():
            student.status = 'Graduated'
            student.save()

            grad_year = timezone.now().year
            alumni, created = AlumniProfile.objects.get_or_create(
                student=student,
                defaults={
                    'graduation_year': grad_year,
                    'degree_awarded': f"{prog.get_degree_level_display()} in {prog.name}",
                    'engagement_notes': f"Graduated with CGPA {student.cgpa:.2f} under Regulation {reg.code}."
                }
            )

        return {
            'success': True,
            'status': 'Graduated',
            'degree': f"{prog.name}",
            'cgpa': student.cgpa,
            'graduation_year': grad_year,
            'alumni_id': alumni.id
        }
