from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from datetime import date

from .models import (
    CustomUser, Course, Subject, Session, Student, Staff,
    StudentPlacement, StudentAchievement,
    FacultyPublication, FacultyTraining, FacultyPatent,
    FeePayment, CollegeExpense, DepartmentBudget,
    NAACCriterion, NAACMetricData,
    NBAProgram, ProgramEducationalObjective, ProgramOutcome,
    ProgramSpecificOutcome, CourseOutcome, COPOMapping,
    COAttainmentRecord, ContinuousImprovementAction,
    InstitutionalDocument, SystemAuditLog, StudentResult, StudentFeeAccount
)
from .decorators import role_required
from .obe_engine import OBEEngine
from .sar_export import SARExportEngine
from .naac_automation import sync_all_naac_criteria, sync_criterion


def seed_naac_criteria_if_needed():
    """Ensure standard 7 NAAC criteria exist."""
    standard_criteria = [
        (1, "Curricular Aspects", 100, "Curricular planning, academic flexibility, curriculum enrichment, and feedback systems."),
        (2, "Teaching-Learning and Evaluation", 350, "Student enrollment, diversity, student-teacher ratio, teaching methods, and evaluation processes."),
        (3, "Research, Innovations and Extension", 110, "Resource mobilization, innovation ecosystem, research publications, patents, and extension activities."),
        (4, "Infrastructure and Learning Resources", 100, "Physical facilities, library as a learning resource, IT infrastructure, and campus maintenance."),
        (5, "Student Support and Progression", 140, "Student mentoring, scholarships, capacity building, student placement, and alumni engagement."),
        (6, "Governance, Leadership and Management", 100, "Institutional vision, strategy, faculty empowerment, financial management, and IQAC quality assurance."),
        (7, "Institutional Values and Best Practices", 100, "Institutional values, gender equity, environmental consciousness, best practices, and distinctiveness."),
    ]
    for num, name, weight, desc in standard_criteria:
        NAACCriterion.objects.get_or_create(
            criterion_number=num,
            defaults={'name': name, 'weightage': weight, 'description': desc}
        )


@role_required(['7', '4', '1'])
def accreditation_home(request):
    """
    Central Accreditation Dashboard (NAAC & NBA overview).
    """
    seed_naac_criteria_if_needed()
    criteria = NAACCriterion.objects.all().order_by('criterion_number')
    nba_programs = NBAProgram.objects.all()

    # Calculate NAAC completeness
    total_metrics = NAACMetricData.objects.count()
    verified_metrics = NAACMetricData.objects.filter(is_verified=True).count()
    naac_pct = round((verified_metrics / total_metrics * 100), 1) if total_metrics > 0 else 0

    # Auto-Aggregated Institutional Facts
    total_students = Student.objects.filter(status='Active').count()
    total_faculty = Staff.objects.filter(employment_status='Active').count()
    sfr = round(total_students / total_faculty, 1) if total_faculty > 0 else 0
    total_pubs = FacultyPublication.objects.count()
    total_patents = FacultyPatent.objects.count()
    total_placements = StudentPlacement.objects.count()

    context = {
        'page_title': 'Accreditation Management Center (NAAC & NBA)',
        'criteria': criteria,
        'nba_programs': nba_programs,
        'total_metrics': total_metrics,
        'verified_metrics': verified_metrics,
        'naac_pct': naac_pct,
        'total_students': total_students,
        'total_faculty': total_faculty,
        'sfr': sfr,
        'total_pubs': total_pubs,
        'total_patents': total_patents,
        'total_placements': total_placements,
    }
    return render(request, 'accreditation_template/accreditation_home.html', context)


CRITERION_RESPONSIBILITY_MAP = {
    1: {
        "title": "Curricular Aspects",
        "owning_sections": "Academic Section, Academic Departments, HODs",
        "data_submitter": "Department NAAC Coordinators / HODs",
        "internal_reviewer": "Curriculum Committee / Accreditation Coordinator",
        "iqac_validator": "IQAC Coordinator",
        "final_approver": "Principal",
        "evidence_guidance": "Syllabus copies, BOS minutes, academic calendars, curriculum feedback forms, analysis reports."
    },
    2: {
        "title": "Teaching-Learning and Evaluation",
        "owning_sections": "HODs, Faculty Members, Examination Section",
        "data_submitter": "Course Instructors / Examination Cell",
        "internal_reviewer": "Academic Audit Committee",
        "iqac_validator": "IQAC Coordinator",
        "final_approver": "Principal",
        "evidence_guidance": "Student-faculty ratio sheets, attendance registers, internal assessment rubrics, end-semester exam result sheets."
    },
    3: {
        "title": "Research, Innovations and Extension",
        "owning_sections": "Research Coordinator, Faculty, Department R&D Cells",
        "data_submitter": "Faculty Researchers / Department R&D Coordinators",
        "internal_reviewer": "Dean (R&D) / Research Committee",
        "iqac_validator": "IQAC Coordinator",
        "final_approver": "Principal",
        "evidence_guidance": "Scopus/WoS publication links, DOI certificates, patent grant certificates, seed grant orders, MoUs."
    },
    4: {
        "title": "Infrastructure and Learning Resources",
        "owning_sections": "Infrastructure Section, Central Library, IT & Computer Center",
        "data_submitter": "Librarian / Systems Admin / Estate Officer",
        "internal_reviewer": "Library & IT Committee",
        "iqac_validator": "IQAC Coordinator",
        "final_approver": "Principal",
        "evidence_guidance": "Library ILMS automation screenshots, stock verification logs, internet bandwidth certificates, AMC orders."
    },
    5: {
        "title": "Student Support and Progression",
        "owning_sections": "Student Welfare Section, Training & Placement Cell, Scholarship Cell",
        "data_submitter": "TPO / Student Welfare Officer / Scholarship Officer",
        "internal_reviewer": "Student Affairs Committee",
        "iqac_validator": "IQAC Coordinator",
        "final_approver": "Principal",
        "evidence_guidance": "Placement offer letters, competitive exam scorecards (GATE/GRE), higher studies admission letters, scholarship disbursal lists."
    },
    6: {
        "title": "Governance, Leadership and Management",
        "owning_sections": "Principal's Office, Administration, HR Section, Finance Section",
        "data_submitter": "Administrative Officer / Finance Officer / HR Coordinator",
        "internal_reviewer": "Governing Body / IQAC Core Team",
        "iqac_validator": "IQAC Coordinator",
        "final_approver": "Principal",
        "evidence_guidance": "Strategic plan documents, audited financial statements, budget sanction orders, faculty appraisal records, IQAC minutes."
    },
    7: {
        "title": "Institutional Values and Best Practices",
        "owning_sections": "IQAC Coordinator, Green Campus Committee, Ethics & Distinctiveness Cell",
        "data_submitter": "IQAC Lead / Committee Conveners",
        "internal_reviewer": "Institutional Values Committee",
        "iqac_validator": "IQAC Coordinator",
        "final_approver": "Principal",
        "evidence_guidance": "Energy audit / green audit reports, gender equity event photos, institutional distinctiveness write-ups, best practice case studies."
    }
}


# ==============================================================================
# NAAC ACCREDITATION MANAGEMENT
# ==============================================================================

@role_required(['7', '4', '1'])
def naac_criterion_detail(request, criterion_id):
    criterion = get_object_or_404(NAACCriterion, id=criterion_id)
    metrics = criterion.metrics.all().order_by('metric_code')
    courses = Course.objects.all()
    responsibility_info = CRITERION_RESPONSIBILITY_MAP.get(criterion.criterion_number, {})

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_metric':
            code = request.POST.get('metric_code')
            title = request.POST.get('title')
            desc = request.POST.get('description', '')
            acad_year = request.POST.get('academic_year', '2024-2025')
            dept_id = request.POST.get('department')
            responsible_dept = request.POST.get('responsible_department', '')
            quant_val = float(request.POST.get('quantitative_value') or 0.0)
            notes = request.POST.get('qualitative_notes', '')
            doc = request.FILES.get('supporting_document')

            dept = Course.objects.filter(id=dept_id).first() if dept_id else None

            NAACMetricData.objects.create(
                criterion=criterion,
                metric_code=code,
                title=title,
                description=desc,
                academic_year=acad_year,
                department=dept,
                responsible_department=responsible_dept or (responsibility_info.get('owning_sections', '')),
                responsible_owner=request.user,
                stage="DATA_ENTRY",
                quantitative_value=quant_val,
                qualitative_notes=notes,
                supporting_document=doc,
            )
            SystemAuditLog.objects.create(
                user=request.user,
                action="NAAC_METRIC",
                module="Accreditation",
                description=f"Added NAAC metric {code} in Criterion {criterion.criterion_number}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Metric {code} added successfully.")
            return redirect(reverse('naac_criterion_detail', args=[criterion.id]))

        elif action == 'submit_for_review':
            metric_id = request.POST.get('metric_id')
            metric = get_object_or_404(NAACMetricData, id=metric_id)
            doc = request.FILES.get('supporting_document')
            if doc:
                metric.supporting_document = doc
            notes = request.POST.get('qualitative_notes')
            if notes:
                metric.qualitative_notes = notes
            metric.stage = "SUBMITTED"
            metric.responsible_owner = request.user
            metric.save()
            messages.success(request, f"Metric {metric.metric_code} submitted for peer / coordinator review.")
            return redirect(reverse('naac_criterion_detail', args=[criterion.id]))

        elif action == 'return_correction':
            metric_id = request.POST.get('metric_id')
            reason = request.POST.get('return_reason', '').strip()
            if not reason:
                messages.error(request, "A reason must be provided when returning a metric for correction.")
                return redirect(reverse('naac_criterion_detail', args=[criterion.id]))
            metric = get_object_or_404(NAACMetricData, id=metric_id)
            metric.stage = "RETURNED"
            metric.return_reason = reason
            metric.reviewer = request.user
            metric.is_verified = False
            metric.save()
            messages.warning(request, f"Metric {metric.metric_code} returned for correction with feedback: '{reason}'")
            return redirect(reverse('naac_criterion_detail', args=[criterion.id]))

        elif action == 'verify_internal':
            metric_id = request.POST.get('metric_id')
            comments = request.POST.get('review_comments', '').strip()
            metric = get_object_or_404(NAACMetricData, id=metric_id)
            from django.utils import timezone
            metric.stage = "VERIFIED_INTERNAL"
            metric.reviewer = request.user
            metric.review_comments = comments
            metric.internal_verified_at = timezone.now()
            metric.save()
            messages.success(request, f"Metric {metric.metric_code} verified internally by {request.user}.")
            return redirect(reverse('naac_criterion_detail', args=[criterion.id]))

        elif action == 'approve_principal':
            if str(request.user.user_type) != '4' and not request.user.is_superuser:
                messages.error(request, "Only the Principal can grant final institutional approval for NAAC metrics.")
                return redirect(reverse('naac_criterion_detail', args=[criterion.id]))
            metric_id = request.POST.get('metric_id')
            metric = get_object_or_404(NAACMetricData, id=metric_id)
            from django.utils import timezone
            metric.stage = "APPROVED_PRINCIPAL"
            metric.is_verified = True
            metric.verified_by = request.user
            metric.principal_approved_at = timezone.now()
            metric.save()
            messages.success(request, f"Metric {metric.metric_code} granted final institutional approval by Principal.")
            return redirect(reverse('naac_criterion_detail', args=[criterion.id]))

        elif action == 'verify_metric':
            metric_id = request.POST.get('metric_id')
            decision = request.POST.get('decision') == 'true'
            metric = get_object_or_404(NAACMetricData, id=metric_id)
            metric.is_verified = decision
            metric.verified_by = request.user if decision else None
            metric.stage = "APPROVED_PRINCIPAL" if decision else "DATA_ENTRY"
            metric.save()

            status_str = "Verified" if decision else "Unverified"
            messages.success(request, f"Metric {metric.metric_code} status set to {status_str}.")
            return redirect(reverse('naac_criterion_detail', args=[criterion.id]))

        elif action == 'auto_sync':
            # Automatically populate quantitative values from database
            sync_naac_data_from_erp(criterion)
            messages.success(request, f"Auto-synced live institutional data into Criterion {criterion.criterion_number}.")
            return redirect(reverse('naac_criterion_detail', args=[criterion.id]))

    context = {
        'page_title': f'NAAC Criterion {criterion.criterion_number}: {criterion.name}',
        'criterion': criterion,
        'metrics': metrics,
        'courses': courses,
        'responsibility_info': responsibility_info,
    }
    return render(request, 'accreditation_template/naac_criterion_detail.html', context)


def sync_naac_data_from_erp(criterion):
    """
    Intelligent cross-module synchronization for NAAC criteria.
    Delegates to NAAC automation engine.
    """
    return sync_criterion(criterion)


@role_required(['7', '4', '1'])
def naac_report(request):
    """Generate consolidated NAAC institutional summary report."""
    criteria = NAACCriterion.objects.all().order_by('criterion_number')
    report_data = []
    for c in criteria:
        metrics = c.metrics.all()
        report_data.append({
            'criterion': c,
            'metrics': metrics,
            'total': metrics.count(),
            'verified': metrics.filter(is_verified=True).count(),
        })

    context = {
        'page_title': 'NAAC Self-Study Report (SSR) Data Summary',
        'report_data': report_data,
        'generation_date': date.today(),
    }
    return render(request, 'accreditation_template/naac_report.html', context)


# ==============================================================================
# NBA ACCREDITATION MANAGEMENT (OUTCOME-BASED EDUCATION)
# ==============================================================================

@role_required(['7', '4', '1', '2'])
def nba_programs_list(request):
    programs = NBAProgram.objects.select_related('course', 'coordinator').all()
    courses = Course.objects.all()
    staff_members = Staff.objects.all()

    # Auto-initialize NBA programs for existing courses if missing
    for c in courses:
        NBAProgram.objects.get_or_create(
            course=c,
            defaults={'program_name': f"B.Tech in {c.name}"}
        )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_program':
            prog_id = request.POST.get('program_id')
            coord_id = request.POST.get('coordinator')
            tier = request.POST.get('tier', 'Tier II')
            prog = get_object_or_404(NBAProgram, id=prog_id)
            prog.coordinator = Staff.objects.filter(id=coord_id).first() if coord_id else None
            prog.tier = tier
            prog.save()
            messages.success(request, f"Updated NBA Program {prog.program_name}.")
            return redirect(reverse('nba_programs_list'))

    context = {
        'page_title': 'NBA Accreditation Programs (OBE)',
        'programs': programs,
        'courses': courses,
        'staff_members': staff_members,
    }
    return render(request, 'accreditation_template/nba_programs.html', context)


@role_required(['7', '4', '1', '2'])
def nba_program_detail(request, program_id):
    program = get_object_or_404(NBAProgram, id=program_id)
    peos = program.peos.all().order_by('code')
    pos = program.pos.all().order_by('code')
    psos = program.psos.all().order_by('code')
    subjects = Subject.objects.filter(course=program.course)
    actions = program.improvement_actions.all().order_by('-created_at')

    # Seed Standard NBA POs (PO1 to PO12) if none exist
    if pos.count() == 0:
        seed_standard_nba_pos(program)
        pos = program.pos.all().order_by('code')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_peo':
            code = request.POST.get('code')
            title = request.POST.get('title')
            desc = request.POST.get('description')
            ProgramEducationalObjective.objects.create(program=program, code=code, title=title, description=desc)
            messages.success(request, f"PEO {code} created.")
            return redirect(reverse('nba_program_detail', args=[program.id]))

        elif action == 'add_pso':
            code = request.POST.get('code')
            title = request.POST.get('title')
            desc = request.POST.get('description')
            ProgramSpecificOutcome.objects.create(program=program, code=code, title=title, description=desc)
            messages.success(request, f"PSO {code} created.")
            return redirect(reverse('nba_program_detail', args=[program.id]))

        elif action == 'add_action_taken':
            out_type = request.POST.get('outcome_type')
            out_code = request.POST.get('outcome_code')
            target = float(request.POST.get('target_level') or 2.5)
            attained = float(request.POST.get('attained_level') or 0.0)
            prop = request.POST.get('action_proposed')
            taken = request.POST.get('action_taken', '')
            status = request.POST.get('status', 'Proposed')

            ContinuousImprovementAction.objects.create(
                program=program,
                outcome_type=out_type,
                outcome_code=out_code,
                target_level=target,
                attained_level=attained,
                action_proposed=prop,
                action_taken=taken,
                status=status
            )
            messages.success(request, f"Continuous improvement action on {out_code} recorded.")
            return redirect(reverse('nba_program_detail', args=[program.id]))

    context = {
        'page_title': f'NBA OBE Management - {program.program_name}',
        'program': program,
        'peos': peos,
        'pos': pos,
        'psos': psos,
        'subjects': subjects,
        'actions': actions,
    }
    return render(request, 'accreditation_template/nba_program_detail.html', context)


def seed_standard_nba_pos(program):
    standard_pos = [
        ("PO1", "Engineering Knowledge", "Apply knowledge of mathematics, science, and engineering fundamentals."),
        ("PO2", "Problem Analysis", "Identify, formulate, and analyze complex engineering problems."),
        ("PO3", "Design/Development of Solutions", "Design solutions for complex engineering problems and systems."),
        ("PO4", "Conduct Investigations of Complex Problems", "Use research-based knowledge and research methods."),
        ("PO5", "Modern Tool Usage", "Create, select, and apply appropriate techniques, resources, and modern tools."),
        ("PO6", "The Engineer and Society", "Apply reasoning informed by contextual knowledge to societal responsibilities."),
        ("PO7", "Environment and Sustainability", "Understand the impact of professional engineering solutions in societal contexts."),
        ("PO8", "Ethics", "Apply ethical principles and commit to professional ethics and responsibilities."),
        ("PO9", "Individual and Team Work", "Function effectively as an individual, and as a member or leader in diverse teams."),
        ("PO10", "Communication", "Communicate effectively on complex engineering activities."),
        ("PO11", "Project Management and Finance", "Demonstrate knowledge and understanding of engineering and management principles."),
        ("PO12", "Life-long Learning", "Recognize the need for, and have the preparation and ability to engage in independent and life-long learning."),
    ]
    for code, title, desc in standard_pos:
        ProgramOutcome.objects.get_or_create(program=program, code=code, defaults={'title': title, 'description': desc})


# ==============================================================================
# CO-PO MAPPING MATRIX & ATTAINMENT ENGINE
# ==============================================================================

@role_required(['7', '4', '1', '2'])
def subject_co_po_mapping(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    program = NBAProgram.objects.filter(course=subject.course).first()
    cos = subject.course_outcomes.all().order_by('code')
    pos = program.pos.all().order_by('code') if program else []
    psos = program.psos.all().order_by('code') if program else []

    # Matrix data structure: {co_id: {po_id: correlation}}
    mappings = COPOMapping.objects.filter(course_outcome__subject=subject)
    matrix = {}
    for m in mappings:
        co_id = m.course_outcome.id
        if co_id not in matrix:
            matrix[co_id] = {'pos': {}, 'psos': {}}
        if m.po:
            matrix[co_id]['pos'][m.po.id] = m.correlation_level
        if m.pso:
            matrix[co_id]['psos'][m.pso.id] = m.correlation_level

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_co':
            code = request.POST.get('code')
            desc = request.POST.get('description')
            target = float(request.POST.get('target_percentage') or 60.0)
            attain_target = float(request.POST.get('attainment_target_students_percentage') or 70.0)
            CourseOutcome.objects.create(
                subject=subject, code=code, description=desc,
                target_percentage=target, attainment_target_students_percentage=attain_target
            )
            messages.success(request, f"Course Outcome {code} defined.")
            return redirect(reverse('subject_co_po_mapping', args=[subject.id]))

        elif action == 'save_mapping':
            # Save matrix values from form
            for co in cos:
                for po in pos:
                    val = int(request.POST.get(f"map_po_{co.id}_{po.id}") or 0)
                    COPOMapping.objects.update_or_create(
                        course_outcome=co, po=po,
                        defaults={'correlation_level': val}
                    )
                for pso in psos:
                    val = int(request.POST.get(f"map_pso_{co.id}_{pso.id}") or 0)
                    COPOMapping.objects.update_or_create(
                        course_outcome=co, pso=pso,
                        defaults={'correlation_level': val}
                    )
            messages.success(request, "CO-PO and CO-PSO mapping matrix updated!")
            return redirect(reverse('subject_co_po_mapping', args=[subject.id]))

        elif action == 'calculate_attainment':
            # Run Attainment Calculation Engine
            calculate_subject_attainment(subject)
            messages.success(request, f"CO-PO Attainment calculated for {subject.name}!")
            return redirect(reverse('subject_co_po_mapping', args=[subject.id]))

    # Retrieve existing attainment records
    attainments = COAttainmentRecord.objects.filter(subject=subject).select_related('course_outcome')

    context = {
        'page_title': f'CO-PO Mapping & Attainment - {subject.name}',
        'subject': subject,
        'program': program,
        'cos': cos,
        'pos': pos,
        'psos': psos,
        'matrix': matrix,
        'attainments': attainments,
    }
    return render(request, 'accreditation_template/co_po_mapping.html', context)


def calculate_subject_attainment(subject, direct_weight=0.80, indirect_weight=0.20, session=None):
    """
    Computes direct and indirect CO attainment based on actual student results
    using configurable institution-approved OBE methodology via OBEEngine.
    """
    if not session:
        session = Session.objects.first()
    if not session:
        return []
    return OBEEngine.compute_subject_co_attainments(
        subject=subject,
        session=session,
        direct_weight=direct_weight,
        indirect_weight=indirect_weight
    )


@role_required(['7', '4', '1', '2', '8'])
def nba_sar_export(request, program_id):
    """
    Self Assessment Report (SAR) Data Export Endpoint.
    Supports ?format=json (default) and ?format=csv.
    """
    format_type = request.GET.get('format', 'json').lower()
    program = get_object_or_404(NBAProgram, id=program_id)
    academic_year = request.GET.get('academic_year')

    if format_type == 'csv':
        csv_data = SARExportEngine.export_sar_csv(program, academic_year=academic_year)
        response = HttpResponse(csv_data, content_type='text/csv; charset=utf-8')
        course_name = program.course.name.replace(' ', '_') if program.course else f"Prog_{program.id}"
        response['Content-Disposition'] = f'attachment; filename="NBA_SAR_{course_name}_{academic_year or "current"}.csv"'
        return response
    else:
        json_data = SARExportEngine.export_sar_json(program, academic_year=academic_year)
        response = HttpResponse(json_data, content_type='application/json; charset=utf-8')
        if request.GET.get('download') == '1':
            course_name = program.course.name.replace(' ', '_') if program.course else f"Prog_{program.id}"
            response['Content-Disposition'] = f'attachment; filename="NBA_SAR_{course_name}_{academic_year or "current"}.json"'
        return response

