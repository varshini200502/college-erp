import json
import math
from datetime import datetime, date
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404, redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import (
    Student, Course, Subject, Session, CustomUser,
    Attendance, AttendanceReport, StudentResult,
    LeaveReportStudent, FeedbackStudent, NotificationStudent,
    Book, FeeStructure, StudentFeeAccount, FeePayment,
    StudentAchievement, StudentPlacement, SystemAuditLog
)
from .decorators import role_required


@role_required(['3'])
def student_home(request):
    student = get_object_or_404(Student, admin=request.user)
    subjects = Subject.objects.filter(course=student.course)
    total_subject = subjects.count()
    total_attendance = AttendanceReport.objects.filter(student=student).count()
    total_present = AttendanceReport.objects.filter(student=student, status=True).count()

    if total_attendance == 0:
        percent_present = 0
        percent_absent = 0
    else:
        percent_present = math.floor((total_present / total_attendance) * 100)
        percent_absent = math.ceil(100 - percent_present)

    subject_attendance_summary = []
    subject_name = []
    data_present = []
    data_absent = []

    for subject in subjects:
        total_sub_att = AttendanceReport.objects.filter(
            attendance__subject=subject, student=student
        ).count()
        present_count = AttendanceReport.objects.filter(
            attendance__subject=subject, status=True, student=student
        ).count()
        absent_count = total_sub_att - present_count

        pct = round((present_count / total_sub_att * 100), 1) if total_sub_att > 0 else 0
        subject_attendance_summary.append({
            'subject': subject,
            'total_classes': total_sub_att,
            'attended': present_count,
            'percentage': pct,
            'is_shortage': pct < 75.0 and total_sub_att > 0
        })

        subject_name.append(subject.name)
        data_present.append(present_count)
        data_absent.append(absent_count)

    # Fee Account summary
    fee_account = getattr(student, 'fee_account', None)

    # Academic Results
    results = StudentResult.objects.filter(student=student)

    # Achievements & Placements
    achievements = student.achievements.all().order_by('-date')[:5]
    placements = student.placements.all()

    context = {
        'page_title': f'Student Dashboard - {student.admin.first_name} {student.admin.last_name}',
        'student': student,
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_subject': total_subject,
        'subject_attendance_summary': subject_attendance_summary,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': subject_name,
        'fee_account': fee_account,
        'results': results,
        'achievements': achievements,
        'placements': placements,
    }
    return render(request, 'student_template/erpnext_student_home.html', context)


# ==============================================================================
# SUBJECT-WISE ATTENDANCE
# ==============================================================================

@csrf_exempt
@role_required(['3'])
def student_view_attendance(request):
    student = get_object_or_404(Student, admin=request.user)
    if request.method != 'POST':
        course = get_object_or_404(Course, id=student.course.id)
        context = {
            'subjects': Subject.objects.filter(course=course),
            'page_title': 'Subject-wise Attendance Details'
        }
        return render(request, 'student_template/student_view_attendance.html', context)
    else:
        subject_id = request.POST.get('subject')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            attendance = Attendance.objects.filter(
                date__range=(start_date, end_date), subject=subject)
            attendance_reports = AttendanceReport.objects.filter(
                attendance__in=attendance, student=student)
            json_data = []
            for report in attendance_reports:
                data = {
                    "date": str(report.attendance.date),
                    "status": report.status,
                    "attendance_status": report.attendance_status
                }
                json_data.append(data)
            return JsonResponse(json.dumps(json_data), safe=False)
        except Exception:
            return JsonResponse([], safe=False)


# ==============================================================================
# MARKS & ACADEMIC RESULTS
# ==============================================================================

@role_required(['3'])
def student_view_result(request):
    student = get_object_or_404(Student, admin=request.user)
    results = StudentResult.objects.filter(student=student).select_related('subject')

    total_marks_obtained = sum(r.total for r in results)
    max_marks_total = len(results) * 100 if len(results) > 0 else 0
    overall_percentage = round((total_marks_obtained / max_marks_total * 100), 1) if max_marks_total > 0 else 0

    context = {
        'student': student,
        'results': results,
        'total_marks_obtained': total_marks_obtained,
        'max_marks_total': max_marks_total,
        'overall_percentage': overall_percentage,
        'page_title': "Academic Results & Internal Assessment"
    }
    return render(request, "student_template/student_view_result.html", context)


# ==============================================================================
# FEES & PAYMENT HISTORY
# ==============================================================================

@role_required(['3'])
def student_view_fees(request):
    student = get_object_or_404(Student, admin=request.user)
    fee_account = getattr(student, 'fee_account', None)

    if not fee_account:
        fs = FeeStructure.objects.filter(course=student.course).first()
        fee_account = StudentFeeAccount.objects.create(student=student, fee_structure=fs)
        fee_account.recalculate()

    payments = fee_account.payments.all().order_by('-payment_date')

    context = {
        'page_title': 'Fee Account & Payment History',
        'student': student,
        'fee_account': fee_account,
        'payments': payments,
    }
    return render(request, "student_template/student_view_fees.html", context)


# ==============================================================================
# ACHIEVEMENTS, INTERNSHIPS, PLACEMENTS PORTFOLIO
# ==============================================================================

@role_required(['3'])
def student_portfolio(request):
    student = get_object_or_404(Student, admin=request.user)
    achievements = student.achievements.all().order_by('-date')
    placements = student.placements.all().order_by('-offer_date')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_achievement':
            cat = request.POST.get('category', 'Certification')
            title = request.POST.get('title')
            event = request.POST.get('event_name', '')
            org = request.POST.get('organization', '')
            ach_date = request.POST.get('date') or str(date.today())
            desc = request.POST.get('description', '')
            cert = request.FILES.get('certificate')

            StudentAchievement.objects.create(
                student=student, category=cat, title=title,
                event_name=event, organization=org, date=ach_date,
                description=desc, certificate=cert
            )
            SystemAuditLog.objects.create(
                user=request.user,
                action="ACHIEVEMENT",
                module="Student",
                description=f"Student {student} recorded achievement: [{cat}] {title}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Achievement '{title}' recorded successfully!")
            return redirect(reverse('student_portfolio'))

        elif action == 'add_placement':
            company = request.POST.get('company_name')
            role = request.POST.get('designation', 'Software Engineer')
            pkg = float(request.POST.get('package_lpa') or 0.0)
            off_date = request.POST.get('offer_date') or str(date.today())
            letter = request.FILES.get('offer_letter')
            is_hs = request.POST.get('is_higher_studies') == 'true'
            inst = request.POST.get('institution_name', '')
            exam = request.POST.get('qualifying_exam', '')

            StudentPlacement.objects.create(
                student=student, company_name=company, designation=role,
                package_lpa=pkg, offer_date=off_date, offer_letter=letter,
                is_higher_studies=is_hs, institution_name=inst, qualifying_exam=exam
            )
            messages.success(request, "Placement / Progression record submitted!")
            return redirect(reverse('student_portfolio'))

    context = {
        'page_title': 'My Achievements, Internships & Placements',
        'student': student,
        'achievements': achievements,
        'placements': placements,
    }
    return render(request, "student_template/student_portfolio.html", context)


# ==============================================================================
# EXISTING STUDENT VIEWS PRESERVED
# ==============================================================================

def student_apply_leave(request):
    form = LeaveReportStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStudent.objects.filter(student=student).order_by('-created_at'),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(request, "Application for leave has been submitted for review")
                return redirect(reverse('student_apply_leave'))
            except Exception:
                messages.error(request, "Could not submit")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_apply_leave.html", context)


def student_feedback(request):
    form = FeedbackStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStudent.objects.filter(student=student).order_by('-created_at'),
        'page_title': 'Student Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_feedback.html", context)


def student_view_profile(request):
    student = get_object_or_404(Student, admin=request.user)
    form = StudentEditForm(request.POST or None, request.FILES or None, instance=student)
    context = {'form': form, 'page_title': 'View/Edit Profile', 'student': student}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = student.admin
                if password:
                    admin.set_password(password)
                if passport:
                    try:
                        fs = FileSystemStorage()
                        filename = fs.save(passport.name, passport)
                        admin.profile_pic = fs.url(filename)
                    except Exception:
                        pass
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                student.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('student_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, f"Error Occurred While Updating Profile: {e}")
    return render(request, "student_template/student_view_profile.html", context)


@csrf_exempt
def student_fcmtoken(request):
    token = request.POST.get('token')
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception:
        return HttpResponse("False")


def student_view_notification(request):
    student = get_object_or_404(Student, admin=request.user)
    notifications = NotificationStudent.objects.filter(student=student).order_by('-created_at')
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)


def view_books(request):
    books = Book.objects.all()
    context = {
        'books': books,
        'page_title': "Library Books"
    }
    return render(request, "student_template/view_books.html", context)
