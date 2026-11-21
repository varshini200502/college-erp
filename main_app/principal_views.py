"""
Principal Views (Phases 1, 2, 3, 4, 5, 8)
Executive Institution-wide Dashboard, Student & Faculty Directories with Detailed Profiles,
Project Domain Innovation Analytics, International Progression, and NAAC/NBA Oversight.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied

from .models import (
    CustomUser, Student, Staff, Course, Subject, Session,
    Attendance, AttendanceReport, StudentResult, StudentPlacement,
    StudentAchievement, FacultyPublication, FacultyTraining, FacultyPatent,
    FeeStructure, StudentFeeAccount, FeePayment, CollegeExpense, DepartmentBudget,
    Payroll, NAACCriterion, NAACMetricData, NBAProgram, SystemAuditLog,
    AlumniProfile, Department, Programme, Batch, Section, StudentProject,
    StudentInternship, StudentOverseasProgression, FacultyInternationalContribution,
    StudentAcademicHistory, HODAppointment
)
from .decorators import role_required


@role_required(['4'])
def principal_home(request):
    """
    Executive Institution-wide Dashboard for the Principal.
    Provides real-time aggregated metrics across Academic, Faculty,
    Student, Projects, International Progression, Finance, and Accreditation.
    """
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='Active').count()
    total_faculty = Staff.objects.count()
    active_faculty = Staff.objects.filter(employment_status='Active').count()
    total_courses = Course.objects.all().count()
    total_subjects = Subject.objects.all().count()

    # Student to Faculty Ratio
    sfr = round(active_students / active_faculty, 1) if active_faculty > 0 else 0

    # Financial Summaries
    total_fee_collected = FeePayment.objects.filter(is_refunded=False).aggregate(s=Sum('amount_paid'))['s'] or 0.0
    total_expenses = CollegeExpense.objects.aggregate(s=Sum('amount'))['s'] or 0.0
    total_fee_due = StudentFeeAccount.objects.aggregate(s=Sum('due_amount'))['s'] or 0.0

    # Project and Innovation Metrics
    total_projects = StudentProject.objects.count()
    active_projects = StudentProject.objects.filter(lifecycle_status__in=['In Progress', 'Approved']).count()
    completed_projects = StudentProject.objects.filter(lifecycle_status__in=['Completed', 'Published/Awarded']).count()
    domain_count = StudentProject.objects.values('technical_domain').distinct().count()

    # International Progression Metrics
    student_overseas_count = StudentOverseasProgression.objects.count()
    faculty_international_count = FacultyInternationalContribution.objects.count()

    # Placement Stats
    placements_count = StudentPlacement.objects.filter(is_higher_studies=False).count()
    higher_studies_count = StudentPlacement.objects.filter(is_higher_studies=True).count()
    avg_package = StudentPlacement.objects.filter(is_higher_studies=False).aggregate(a=Avg('package_lpa'))['a'] or 0.0

    # Research & Faculty Contributions
    total_publications = FacultyPublication.objects.count()
    total_patents = FacultyPatent.objects.count()
    total_fdps = FacultyTraining.objects.count()

    # Department-wise Breakdown (bulk group-by queries to eliminate N+1 loops)
    courses = list(Course.objects.all().order_by('id'))
    stu_by_course = dict(Student.objects.filter(status='Active').values('course_id').annotate(c=Count('id')).values_list('course_id', 'c'))
    staff_by_course = dict(Staff.objects.filter(employment_status='Active').values('course_id').annotate(c=Count('id')).values_list('course_id', 'c'))

    dept_stats = []
    for c in courses:
        s_count = stu_by_course.get(c.id, 0)
        f_count = staff_by_course.get(c.id, 0)
        p_count = StudentProject.objects.filter(Q(primary_programme__department__code=c.name) | Q(guide__course=c)).count()
        dept_stats.append({
            'course': c,
            'students': s_count,
            'faculty': f_count,
            'projects': p_count,
        })

    # NAAC Completeness
    naac_metrics_total = NAACMetricData.objects.count()
    naac_metrics_verified = NAACMetricData.objects.filter(is_verified=True).count()
    naac_readiness = round((naac_metrics_verified / naac_metrics_total * 100), 1) if naac_metrics_total > 0 else 0

    # Alumni Statistics
    total_alumni = AlumniProfile.objects.count()
    notable_alumni = AlumniProfile.objects.filter(is_notable=True).count()

    # Recent Audit Logs
    recent_logs = SystemAuditLog.objects.order_by('-timestamp')[:8]

    context = {
        'page_title': 'Principal Executive Dashboard',
        'total_students': total_students,
        'active_students': active_students,
        'total_faculty': total_faculty,
        'active_faculty': active_faculty,
        'total_courses': total_courses,
        'total_subjects': total_subjects,
        'sfr': sfr,
        'total_fee_collected': round(total_fee_collected, 2),
        'total_expenses': round(total_expenses, 2),
        'total_fee_due': round(total_fee_due, 2),
        'net_balance': round(total_fee_collected - total_expenses, 2),
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'domain_count': domain_count,
        'student_overseas_count': student_overseas_count,
        'faculty_international_count': faculty_international_count,
        'placements_count': placements_count,
        'higher_studies_count': higher_studies_count,
        'avg_package': round(avg_package, 2),
        'total_publications': total_publications,
        'total_patents': total_patents,
        'total_fdps': total_fdps,
        'dept_stats': dept_stats,
        'naac_readiness': naac_readiness,
        'total_alumni': total_alumni,
        'notable_alumni': notable_alumni,
        'recent_logs': recent_logs,
    }
    return render(request, 'principal_template/principal_home.html', context)


@role_required(['4', '8', '1'])
def principal_view_students(request):
    """
    Institution-wide Student Roster for Principal & Registrar.
    Displays all enrolled students (24 total) with status-filter tabs (Active 17, Alumni 6, Graduated 1).
    """
    status_filter = request.GET.get('status', '')  # Default to empty = all statuses
    course_filter = request.GET.get('course', '')
    search_query = request.GET.get('search', '').strip()

    students = Student.objects.select_related('admin', 'course', 'programme', 'batch', 'fee_account').all()

    total_count = Student.objects.count()
    active_count = Student.objects.filter(status='Active').count()
    alumni_count = Student.objects.filter(status='Alumni').count()
    graduated_count = Student.objects.filter(status='Graduated').count()

    if status_filter:
        students = students.filter(status=status_filter)
    if course_filter:
        students = students.filter(course_id=course_filter)
    if search_query:
        students = students.filter(
            Q(admin__first_name__icontains=search_query) |
            Q(admin__last_name__icontains=search_query) |
            Q(admin__email__icontains=search_query) |
            Q(roll_number__icontains=search_query) |
            Q(admission_number__icontains=search_query)
        )

    students = students.order_by('id')
    paginator = Paginator(students, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    courses = Course.objects.all()
    context = {
        'page_title': 'Institutional Student Roster',
        'students': page_obj,
        'courses': courses,
        'selected_status': status_filter,
        'selected_course': course_filter,
        'search_query': search_query,
        'total_count': total_count,
        'active_count': active_count,
        'alumni_count': alumni_count,
        'graduated_count': graduated_count,
    }
    return render(request, 'principal_template/student_list.html', context)


@role_required(['4', '8', '1', '2'])
def student_profile(request, student_id):
    """
    Comprehensive 7-Section Student Profile View:
    A. Personal & Admission Info
    B. Academic Performance & Results
    C. Multi-Project Portfolio (Lifecycle 1-7)
    D. Internships & Industry Experience
    E. Placement & Career Outcomes
    F. International & Overseas Progression
    G. Achievements & Certifications
    """
    student = get_object_or_404(
        Student.objects.select_related('admin', 'course', 'programme', 'batch', 'academic_section', 'session', 'fee_account'),
        id=student_id
    )

    # Department-level security check for HOD / Faculty (user_type=2)
    if request.user.user_type == '2':
        staff = getattr(request.user, 'staff', None)
        if staff:
            hod_depts = [dept.id for dept in staff.active_hod_departments]
            is_student_dept = (student.programme and student.programme.department_id in hod_depts) or \
                              (student.course and student.course.id in hod_depts)
            if not staff.is_hod or not is_student_dept:
                # Also allow if faculty is the direct guide of the student in any project
                is_guide = StudentProject.objects.filter(students=student, guide=staff).exists()
                if not is_guide:
                    messages.error(request, "Access restricted: You may only view students within your department or guided projects.")
                    return redirect(reverse('staff_home'))

    # Academic Results & Attendance
    results = StudentResult.objects.filter(student=student).select_related('subject')
    attendance_reports = AttendanceReport.objects.filter(student=student).select_related('attendance__subject')
    total_attendance = attendance_reports.count()
    present_attendance = attendance_reports.filter(status=True).count()
    attendance_pct = round((present_attendance / total_attendance * 100), 1) if total_attendance > 0 else 0.0

    academic_history = StudentAcademicHistory.objects.filter(student=student).order_by('semester')

    # Multi-Project Portfolio
    projects = StudentProject.objects.filter(students=student).select_related('primary_programme', 'guide', 'co_guide').prefetch_related('students')

    # Internships
    internships = StudentInternship.objects.filter(student=student).order_by('-start_date')

    # Placements & Career
    placements = StudentPlacement.objects.filter(student=student).order_by('-created_at')

    # International Progression
    overseas_records = StudentOverseasProgression.objects.filter(student=student).order_by('-created_at')

    # Achievements
    achievements = StudentAchievement.objects.filter(student=student).order_by('-date')

    context = {
        'page_title': f"Student Profile — {student.admin.first_name} {student.admin.last_name}",
        'student': student,
        'results': results,
        'total_attendance': total_attendance,
        'present_attendance': present_attendance,
        'attendance_pct': attendance_pct,
        'academic_history': academic_history,
        'projects': projects,
        'internships': internships,
        'placements': placements,
        'overseas_records': overseas_records,
        'achievements': achievements,
    }
    return render(request, 'principal_template/student_profile_detail.html', context)


@role_required(['4', '8', '1'])
def principal_view_faculty(request):
    """
    Institution-wide Faculty Directory for Principal & Registrar.
    Displays faculty members, primary departments, designations, qualifications, and publications.
    """
    dept_filter = request.GET.get('course', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '').strip()

    staff_list = Staff.objects.select_related('admin', 'course', 'primary_department').prefetch_related('publications', 'patents', 'trainings').all()

    total_count = Staff.objects.count()
    active_count = Staff.objects.filter(employment_status='Active').count()

    if dept_filter:
        staff_list = staff_list.filter(Q(course_id=dept_filter) | Q(primary_department_id=dept_filter))
    if status_filter:
        staff_list = staff_list.filter(employment_status=status_filter)
    if search_query:
        staff_list = staff_list.filter(
            Q(admin__first_name__icontains=search_query) |
            Q(admin__last_name__icontains=search_query) |
            Q(admin__email__icontains=search_query) |
            Q(faculty_id__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )

    staff_list = staff_list.order_by('id')
    courses = Course.objects.all()
    departments = Department.objects.filter(is_active=True)

    context = {
        'page_title': 'Institutional Faculty Directory',
        'staff_list': staff_list,
        'courses': courses,
        'departments': departments,
        'selected_course': dept_filter,
        'selected_status': status_filter,
        'search_query': search_query,
        'total_count': total_count,
        'active_count': active_count,
    }
    return render(request, 'principal_template/faculty_list.html', context)


@role_required(['4', '8', '1', '2'])
def faculty_profile(request, staff_id):
    """
    Comprehensive Faculty Profile View:
    - Personal & Employment Details
    - Teaching Load & Assigned Subjects
    - Research, Publications & Patents
    - Faculty Development Programmes (FDPs, STTPs)
    - Student Project Guidance
    - International Contributions
    """
    staff = get_object_or_404(
        Staff.objects.select_related('admin', 'course', 'primary_department'),
        id=staff_id
    )

    # Department-level security check for HOD
    if request.user.user_type == '2' and request.user.id != staff.admin.id:
        current_staff = getattr(request.user, 'staff', None)
        if current_staff:
            hod_depts = [d.id for d in current_staff.active_hod_departments]
            is_staff_dept = (staff.primary_department and staff.primary_department.id in hod_depts) or \
                            (staff.course and staff.course.id in hod_depts)
            if not current_staff.is_hod or not is_staff_dept:
                messages.error(request, "Access restricted to department faculty.")
                return redirect(reverse('staff_home'))

    # Teaching assignments
    subjects = Subject.objects.filter(staff=staff).select_related('course')

    # Research & Publications
    publications = FacultyPublication.objects.filter(staff=staff).order_by('-publication_date')
    patents = FacultyPatent.objects.filter(staff=staff).order_by('-filing_date')

    # Faculty Development
    trainings = FacultyTraining.objects.filter(staff=staff).order_by('-start_date')

    # Student Project Guidance
    guided_projects = StudentProject.objects.filter(Q(guide=staff) | Q(co_guide=staff)).select_related('primary_programme').prefetch_related('students')

    # International Contributions
    international_contributions = FacultyInternationalContribution.objects.filter(staff=staff).order_by('-event_date')

    # HOD Appointments History
    hod_history = HODAppointment.objects.filter(faculty=staff).select_related('department').order_by('-start_date')

    context = {
        'page_title': f"Faculty Profile — {staff.admin.first_name} {staff.admin.last_name}",
        'staff': staff,
        'subjects': subjects,
        'publications': publications,
        'patents': patents,
        'trainings': trainings,
        'guided_projects': guided_projects,
        'international_contributions': international_contributions,
        'hod_history': hod_history,
    }
    return render(request, 'principal_template/faculty_profile_detail.html', context)


@role_required(['4', '8', '1'])
def principal_project_analytics(request):
    """
    Phase 4: Student Project & Innovation Dashboard.
    Provides real-time domain breakdown across the 17 technical domains,
    clickable domain drill-downs, status breakdowns, and project profiles.
    """
    domain_filter = request.GET.get('domain', '').strip()
    status_filter = request.GET.get('status', '').strip()
    dept_filter = request.GET.get('department', '').strip()
    search_query = request.GET.get('search', '').strip()

    projects = StudentProject.objects.select_related('primary_programme', 'guide', 'co_guide').prefetch_related('students').all()

    total_projects = projects.count()
    ongoing_count = projects.filter(lifecycle_status__in=['Proposed', 'Approved', 'In Progress', 'Under Review']).count()
    completed_count = projects.filter(lifecycle_status__in=['Completed', 'Published/Awarded']).count()
    students_participating = Student.objects.filter(projects__isnull=False).distinct().count()

    # The 17 Official Technical Domains
    OFFICIAL_DOMAINS = [
        "Artificial Intelligence and Machine Learning",
        "Computer Vision and Image Processing",
        "Natural Language Processing",
        "Data Science and Analytics",
        "Web Development",
        "Mobile Application Development",
        "Cybersecurity and Ethical Hacking",
        "Cloud Computing",
        "DevOps",
        "Internet of Things",
        "Embedded Systems",
        "Robotics and Automation",
        "Blockchain",
        "Signal Processing",
        "Database Systems",
        "Software Engineering",
        "Interdisciplinary and Other Domains",
    ]

    # Domain Counts
    domain_stats = []
    for d in OFFICIAL_DOMAINS:
        cnt = StudentProject.objects.filter(technical_domain__iexact=d).count()
        domain_stats.append({
            'domain': d,
            'count': cnt,
            'is_active': (domain_filter.lower() == d.lower()) if domain_filter else False
        })

    # Apply filters
    if domain_filter:
        projects = projects.filter(technical_domain__icontains=domain_filter)
    if status_filter:
        projects = projects.filter(lifecycle_status=status_filter)
    if dept_filter:
        projects = projects.filter(primary_programme__department_id=dept_filter)
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(problem_statement__icontains=search_query) |
            Q(technologies__icontains=search_query) |
            Q(students__admin__first_name__icontains=search_query) |
            Q(students__admin__last_name__icontains=search_query)
        ).distinct()

    projects = projects.order_by('-created_at')
    departments = Department.objects.filter(is_active=True)

    context = {
        'page_title': 'Student Projects & Technical Domain Analytics',
        'projects': projects,
        'total_projects': total_projects,
        'ongoing_count': ongoing_count,
        'completed_count': completed_count,
        'students_participating': students_participating,
        'domain_stats': domain_stats,
        'selected_domain': domain_filter,
        'selected_status': status_filter,
        'selected_dept': dept_filter,
        'search_query': search_query,
        'departments': departments,
        'lifecycle_choices': StudentProject.LIFECYCLE_STATUS,
    }
    return render(request, 'principal_template/project_analytics.html', context)


@role_required(['4', '8', '1'])
def principal_international_analytics(request):
    """
    Phase 5: International and Overseas Progression Analytics.
    Provides institution-wide oversight of higher studies abroad, foreign scholarships,
    overseas internships, international research, and faculty international collaborations.
    """
    country_filter = request.GET.get('country', '').strip()
    outcome_filter = request.GET.get('outcome', '').strip()
    search_query = request.GET.get('search', '').strip()

    student_records = StudentOverseasProgression.objects.select_related('student__admin', 'student__course', 'student__programme').all()
    faculty_records = FacultyInternationalContribution.objects.select_related('staff__admin', 'staff__course', 'staff__primary_department').all()

    total_student_overseas = student_records.count()
    total_faculty_intl = faculty_records.count()

    # Distinct countries
    countries_s = list(StudentOverseasProgression.objects.values_list('country', flat=True).distinct())
    countries_f = list(FacultyInternationalContribution.objects.values_list('country', flat=True).distinct())
    all_countries = sorted(list(set(filter(None, countries_s + countries_f))))

    # Outcome breakdown for students
    higher_studies_count = student_records.filter(progression_type='Higher Studies').count()
    internships_count = student_records.filter(progression_type='Overseas Internship').count()
    exchange_count = student_records.filter(progression_type='International Exchange').count()
    employment_count = student_records.filter(progression_type='Overseas Employment').count()

    # Apply filters
    if country_filter:
        student_records = student_records.filter(country__icontains=country_filter)
        faculty_records = faculty_records.filter(country__icontains=country_filter)
    if outcome_filter:
        student_records = student_records.filter(progression_type=outcome_filter)
    if search_query:
        student_records = student_records.filter(
            Q(student__admin__first_name__icontains=search_query) |
            Q(student__admin__last_name__icontains=search_query) |
            Q(foreign_university__icontains=search_query) |
            Q(country__icontains=search_query)
        )
        faculty_records = faculty_records.filter(
            Q(staff__admin__first_name__icontains=search_query) |
            Q(staff__admin__last_name__icontains=search_query) |
            Q(foreign_institution__icontains=search_query) |
            Q(country__icontains=search_query)
        )

    context = {
        'page_title': 'International & Overseas Progression Analytics',
        'student_records': student_records,
        'faculty_records': faculty_records,
        'total_student_overseas': total_student_overseas,
        'total_faculty_intl': total_faculty_intl,
        'higher_studies_count': higher_studies_count,
        'internships_count': internships_count,
        'exchange_count': exchange_count,
        'employment_count': employment_count,
        'all_countries': all_countries,
        'selected_country': country_filter,
        'selected_outcome': outcome_filter,
        'search_query': search_query,
    }
    return render(request, 'principal_template/international_analytics.html', context)


@role_required(['4'])
def principal_view_finance(request):
    """Institutional finance overview for Principal."""
    payments = FeePayment.objects.order_by('-payment_date')[:15]
    expenses = CollegeExpense.objects.order_by('-expense_date')[:15]
    budgets = DepartmentBudget.objects.all()

    total_income = FeePayment.objects.filter(is_refunded=False).aggregate(s=Sum('amount_paid'))['s'] or 0.0
    total_expense = CollegeExpense.objects.aggregate(s=Sum('amount'))['s'] or 0.0

    context = {
        'page_title': 'Institutional Finance Overview',
        'payments': payments,
        'expenses': expenses,
        'budgets': budgets,
        'total_income': round(total_income, 2),
        'total_expense': round(total_expense, 2),
        'surplus': round(total_income - total_expense, 2),
    }
    return render(request, 'principal_template/finance_overview.html', context)


@role_required(['4'])
def principal_view_accreditation(request):
    """Accreditation readiness overview for Principal."""
    criteria = NAACCriterion.objects.all().order_by('criterion_number')
    nba_programs = NBAProgram.objects.all()

    criteria_summary = []
    for c in criteria:
        total = c.metrics.count()
        verified = c.metrics.filter(is_verified=True).count()
        pct = round((verified / total * 100), 1) if total > 0 else 0
        criteria_summary.append({
            'criterion': c,
            'total_metrics': total,
            'verified_metrics': verified,
            'completion_pct': pct
        })

    context = {
        'page_title': 'Accreditation Readiness Overview',
        'criteria_summary': criteria_summary,
        'nba_programs': nba_programs,
    }
    return render(request, 'principal_template/accreditation_overview.html', context)
