from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q

from .models import (
    CustomUser, Student, Staff, Course, Subject, Session,
    Attendance, AttendanceReport, StudentResult, StudentPlacement,
    StudentAchievement, FacultyPublication, FacultyTraining, FacultyPatent,
    FeeStructure, StudentFeeAccount, FeePayment, CollegeExpense, DepartmentBudget,
    Payroll, NAACCriterion, NAACMetricData, NBAProgram, SystemAuditLog,
    AlumniProfile
)
from .decorators import role_required


@role_required(['4'])
def principal_home(request):
    """
    Executive Institution-wide Dashboard for the Principal.
    Provides real-time aggregated metrics across Academic, Faculty,
    Student, Finance, and Accreditation modules.
    """
    total_students = Student.objects.filter(status='Active').count()
    total_faculty = Staff.objects.filter(employment_status='Active').count()
    total_courses = Course.objects.all().count()
    total_subjects = Subject.objects.all().count()

    # Student to Faculty Ratio
    sfr = round(total_students / total_faculty, 1) if total_faculty > 0 else 0

    # Financial Summaries
    total_fee_collected = FeePayment.objects.filter(is_refunded=False).aggregate(s=Sum('amount_paid'))['s'] or 0.0
    total_expenses = CollegeExpense.objects.aggregate(s=Sum('amount'))['s'] or 0.0
    total_fee_due = StudentFeeAccount.objects.aggregate(s=Sum('due_amount'))['s'] or 0.0

    # Placement Stats
    placements_count = StudentPlacement.objects.filter(is_higher_studies=False).count()
    higher_studies_count = StudentPlacement.objects.filter(is_higher_studies=True).count()
    avg_package = StudentPlacement.objects.filter(is_higher_studies=False).aggregate(a=Avg('package_lpa'))['a'] or 0.0

    # Research & Faculty Contributions
    total_publications = FacultyPublication.objects.count()
    total_patents = FacultyPatent.objects.count()
    total_fdps = FacultyTraining.objects.count()

    # Department-wise Breakdown
    courses = Course.objects.all()
    dept_stats = []
    for c in courses:
        s_count = Student.objects.filter(course=c, status='Active').count()
        f_count = Staff.objects.filter(course=c, employment_status='Active').count()
        dept_stats.append({
            'course': c,
            'students': s_count,
            'faculty': f_count,
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
        'total_faculty': total_faculty,
        'total_courses': total_courses,
        'total_subjects': total_subjects,
        'sfr': sfr,
        'total_fee_collected': round(total_fee_collected, 2),
        'total_expenses': round(total_expenses, 2),
        'total_fee_due': round(total_fee_due, 2),
        'net_balance': round(total_fee_collected - total_expenses, 2),
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


@role_required(['4'])
def principal_view_students(request):
    status_filter = request.GET.get('status', 'Active')
    course_filter = request.GET.get('course', '')

    students = Student.objects.all()
    if status_filter:
        students = students.filter(status=status_filter)
    if course_filter:
        students = students.filter(course_id=course_filter)

    courses = Course.objects.all()
    context = {
        'page_title': 'Institutional Student Roster',
        'students': students,
        'courses': courses,
        'selected_status': status_filter,
        'selected_course': course_filter,
    }
    return render(request, 'principal_template/student_list.html', context)


@role_required(['4'])
def principal_view_faculty(request):
    dept_filter = request.GET.get('course', '')
    staff_list = Staff.objects.all()
    if dept_filter:
        staff_list = staff_list.filter(course_id=dept_filter)

    courses = Course.objects.all()
    context = {
        'page_title': 'Institutional Faculty Directory',
        'staff_list': staff_list,
        'courses': courses,
        'selected_course': dept_filter,
    }
    return render(request, 'principal_template/faculty_list.html', context)


@role_required(['4'])
def principal_view_finance(request):
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
