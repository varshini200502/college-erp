import json
from datetime import date
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404, redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import (
    CustomUser, Staff, Student, Course, Subject, Session,
    Attendance, AttendanceReport, AttendanceCorrectionLog,
    StudentResult, MarksCorrectionLog,
    LeaveReportStaff, FeedbackStaff, NotificationStaff,
    Book, IssuedBook,
    FacultyQualification, FacultyPublication, FacultyTraining, FacultyPatent,
    CourseOutcome, SystemAuditLog
)
from .decorators import role_required


@role_required(['2', '1', '4'])
def staff_home(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    total_subject = subjects.count()
    total_students = Student.objects.filter(course=staff.course).count()
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    total_attendance = Attendance.objects.filter(subject__in=subjects).count()

    # Research & Contribution counts
    total_publications = staff.publications.count()
    total_trainings = staff.trainings.count()
    total_patents = staff.patents.count()

    subject_list = []
    attendance_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name)
        attendance_list.append(attendance_count)

    context = {
        'page_title': f'Faculty Portal - {staff.admin.first_name} {staff.admin.last_name} ({staff.designation})',
        'staff': staff,
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_subject': total_subject,
        'total_publications': total_publications,
        'total_trainings': total_trainings,
        'total_patents': total_patents,
        'subject_list': subject_list,
        'attendance_list': attendance_list,
        'assigned_subjects': subjects,
    }
    return render(request, "staff_template/erpnext_staff_home.html", context)


# ==============================================================================
# ATTENDANCE MANAGEMENT & AUDIT LOGS
# ==============================================================================

@role_required(['2', '1', '4'])
def staff_take_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Take Daily Attendance'
    }
    return render(request, 'staff_template/staff_take_attendance.html', context)


@csrf_exempt
def get_students(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        students = Student.objects.filter(course_id=subject.course.id, session=session, status='Active')
        student_data = []
        for student in students:
            data = {
                "id": student.id,
                "name": f"{student.admin.last_name} {student.admin.first_name} (Roll: {student.roll_number or student.id})"
            }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return JsonResponse([], safe=False)


@csrf_exempt
def save_attendance(request):
    student_data = request.POST.get('student_ids')
    att_date = request.POST.get('date')
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')

    if not student_data:
        return HttpResponse("No student data received", status=400)

    students = json.loads(student_data)
    try:
        session = get_object_or_404(Session, id=session_id)
        subject = get_object_or_404(Subject, id=subject_id)
        attendance, _ = Attendance.objects.get_or_create(session=session, subject=subject, date=att_date)

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))
            status_val = bool(student_dict.get('status'))
            AttendanceReport.objects.update_or_create(
                student=student, attendance=attendance,
                defaults={'status': status_val, 'attendance_status': 'Present' if status_val else 'Absent'}
            )
        return HttpResponse("OK")
    except Exception as e:
        return HttpResponse(str(e), status=500)


@role_required(['2', '1', '4'])
def staff_update_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Update Attendance & Audit Log'
    }
    return render(request, 'staff_template/staff_update_attendance.html', context)


@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        att = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=att).select_related('student__admin')
        student_data = []
        for a in attendance_data:
            data = {
                "id": a.student.admin.id,
                "name": f"{a.student.admin.last_name} {a.student.admin.first_name}",
                "status": a.status
            }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return JsonResponse([], safe=False)


@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get('student_ids')
    att_id = request.POST.get('date')
    reason = request.POST.get('reason', 'Routine Attendance Correction')
    students = json.loads(student_data)
    try:
        attendance = get_object_or_404(Attendance, id=att_id)
        for student_dict in students:
            student = get_object_or_404(Student, admin_id=student_dict.get('id'))
            report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)
            new_status = bool(student_dict.get('status'))

            # Check if status changed; if so, create audit log
            if report.status != new_status:
                AttendanceCorrectionLog.objects.create(
                    attendance_report=report,
                    changed_by=request.user,
                    previous_status=report.status,
                    new_status=new_status,
                    reason=reason
                )
                report.status = new_status
                report.attendance_status = 'Present' if new_status else 'Absent'
                report.save()

        return HttpResponse("OK")
    except Exception as e:
        return HttpResponse(str(e), status=500)


# ==============================================================================
# MARKS & ASSESSMENT MANAGEMENT (WITH FINALIZATION LOCK & AUDIT LOG)
# ==============================================================================

@role_required(['2', '1', '4'])
def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    sessions = Session.objects.all()

    context = {
        'page_title': 'Comprehensive Marks & Assessment Entry',
        'subjects': subjects,
        'sessions': sessions
    }

    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            subject_id = request.POST.get('subject')
            test = float(request.POST.get('test') or 0.0)
            exam = float(request.POST.get('exam') or 0.0)
            assignment = float(request.POST.get('assignment') or 0.0)
            practical = float(request.POST.get('practical') or 0.0)
            project = float(request.POST.get('project') or 0.0)
            reason = request.POST.get('reason', 'Marks Entry')

            student = get_object_or_404(Student, id=student_id)
            subject = get_object_or_404(Subject, id=subject_id)

            result, created = StudentResult.objects.get_or_create(
                student=student, subject=subject,
                defaults={
                    'test': test, 'exam': exam,
                    'assignment': assignment, 'practical': practical, 'project': project
                }
            )

            if not created:
                # If finalized, prevent modification unless authorized
                if result.is_finalized and not (request.user.is_superuser or str(request.user.user_type) in ['1', '4']):
                    messages.error(request, "Marks are finalized! Request administrative reopening to modify.")
                    return render(request, "staff_template/staff_add_result.html", context)

                # Record correction audit log
                MarksCorrectionLog.objects.create(
                    result=result,
                    changed_by=request.user,
                    previous_test=result.test,
                    new_test=test,
                    previous_exam=result.exam,
                    new_exam=exam,
                    previous_assignment=result.assignment,
                    new_assignment=assignment,
                    previous_practical=result.practical,
                    new_practical=practical,
                    reason=reason
                )
                result.test = test
                result.exam = exam
                result.assignment = assignment
                result.practical = practical
                result.project = project
                result.save()
                messages.success(request, f"Assessment marks updated with audit log for {student}!")
            else:
                result.save()
                messages.success(request, f"Scores saved for {student}!")

        except Exception as e:
            messages.warning(request, f"Error processing form: {e}")

    return render(request, "staff_template/staff_add_result.html", context)


@csrf_exempt
def fetch_student_result(request):
    try:
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        result = StudentResult.objects.filter(student=student, subject=subject).first()
        if result:
            result_data = {
                'exam': result.exam,
                'test': result.test,
                'assignment': result.assignment,
                'practical': result.practical,
                'project': result.project,
                'total': result.total,
                'is_finalized': result.is_finalized,
            }
        else:
            result_data = {
                'exam': 0, 'test': 0, 'assignment': 0, 'practical': 0, 'project': 0, 'total': 0, 'is_finalized': False
            }
        return JsonResponse(result_data)
    except Exception:
        return JsonResponse({'error': 'Not found'}, status=404)


@role_required(['2', '1', '4'])
def finalize_subject_results(request, subject_id):
    """Lock marks for a subject so they cannot be altered without controlled correction."""
    subject = get_object_or_404(Subject, id=subject_id)
    results = StudentResult.objects.filter(subject=subject)
    for r in results:
        r.is_finalized = True
        r.finalized_at = date.today()
        r.finalized_by = request.user
        r.save()

    SystemAuditLog.objects.create(
        user=request.user,
        action="FINALIZE_MARKS",
        module="Academic",
        description=f"Finalized and locked marks for subject '{subject.name}' ({results.count()} students).",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    messages.success(request, f"Marks for {subject.name} are now finalized and locked.")
    return redirect(reverse('staff_add_result'))


# ==============================================================================
# FACULTY PORTFOLIO: QUALIFICATIONS, PUBLICATIONS, FDPs, PATENTS
# ==============================================================================

@role_required(['2', '1', '4'])
def staff_portfolio(request):
    staff = get_object_or_404(Staff, admin=request.user)
    qualifications = staff.qualifications.all().order_by('-year_of_completion')
    publications = staff.publications.all().order_by('-publication_date')
    trainings = staff.trainings.all().order_by('-start_date')
    patents = staff.patents.all().order_by('-filing_date')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_qualification':
            deg = request.POST.get('degree')
            spec = request.POST.get('specialization')
            inst = request.POST.get('institution')
            year = int(request.POST.get('year_of_completion') or 2020)
            cert = request.FILES.get('certificate')

            FacultyQualification.objects.create(
                staff=staff, degree=deg, specialization=spec,
                institution=inst, year_of_completion=year, certificate=cert
            )
            messages.success(request, f"Qualification '{deg}' added.")
            return redirect(reverse('staff_portfolio'))

        elif action == 'add_publication':
            pub_type = request.POST.get('publication_type', 'Journal')
            title = request.POST.get('title')
            journal = request.POST.get('journal_or_conference_name')
            issn = request.POST.get('issn_isbn', '')
            indexing = request.POST.get('indexing', 'Scopus')
            doi = request.POST.get('doi', '')
            pub_date = request.POST.get('publication_date') or str(date.today())
            acad_year = request.POST.get('academic_year', '2024-2025')
            doc = request.FILES.get('document')

            FacultyPublication.objects.create(
                staff=staff, publication_type=pub_type, title=title,
                journal_or_conference_name=journal, issn_isbn=issn,
                indexing=indexing, doi=doi, publication_date=pub_date,
                academic_year=acad_year, document=doc
            )
            SystemAuditLog.objects.create(
                user=request.user,
                action="PUBLICATION",
                module="Faculty",
                description=f"Faculty {staff} added publication: {title}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Publication '{title}' added! Reusable for NAAC Criterion 3.")
            return redirect(reverse('staff_portfolio'))

        elif action == 'add_training':
            t_type = request.POST.get('training_type', 'FDP')
            role = request.POST.get('role', 'Attended')
            title = request.POST.get('title')
            body = request.POST.get('organizing_body')
            days = int(request.POST.get('duration_days') or 1)
            start = request.POST.get('start_date') or str(date.today())
            end = request.POST.get('end_date') or str(date.today())
            acad_year = request.POST.get('academic_year', '2024-2025')
            cert = request.FILES.get('certificate')

            FacultyTraining.objects.create(
                staff=staff, training_type=t_type, role=role, title=title,
                organizing_body=body, duration_days=days, start_date=start,
                end_date=end, academic_year=acad_year, certificate=cert
            )
            messages.success(request, f"Training/FDP '{title}' recorded.")
            return redirect(reverse('staff_portfolio'))

        elif action == 'add_patent':
            title = request.POST.get('title')
            app_no = request.POST.get('application_number')
            status = request.POST.get('status', 'Filed')
            filing = request.POST.get('filing_date') or str(date.today())
            office = request.POST.get('patent_office', 'Indian Patent Office')
            doc = request.FILES.get('document')

            FacultyPatent.objects.create(
                staff=staff, title=title, application_number=app_no,
                status=status, filing_date=filing, patent_office=office, document=doc
            )
            messages.success(request, f"Patent '{title}' added.")
            return redirect(reverse('staff_portfolio'))

    context = {
        'page_title': 'Faculty Profile & Research Portfolio',
        'staff': staff,
        'qualifications': qualifications,
        'publications': publications,
        'trainings': trainings,
        'patents': patents,
    }
    return render(request, 'staff_template/staff_portfolio.html', context)


# ==============================================================================
# EXISTING STAFF VIEWS PRESERVED
# ==============================================================================

def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStaff.objects.filter(staff=staff).order_by('-created_at'),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)


def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(staff=staff).order_by('-created_at'),
        'page_title': 'Staff Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    form = StaffEditForm(request.POST or None, request.FILES or None, instance=staff)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = staff.admin
                if password:
                    admin.set_password(password)
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    admin.profile_pic = fs.url(filename)
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                staff.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('staff_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, f"Error Occurred While Updating Profile: {e}")
    return render(request, "staff_template/staff_view_profile.html", context)


@csrf_exempt
def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception:
        return HttpResponse("False")


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff).order_by('-created_at')
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)


def add_book(request):
    if request.method == "POST":
        name = request.POST.get('name')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        category = request.POST.get('category')
        Book.objects.create(name=name, author=author, isbn=isbn, category=category)
        return render(request, "staff_template/add_book.html", {'alert': True, 'page_title': 'Add Book'})
    return render(request, "staff_template/add_book.html", {'page_title': "Add Book"})


def issue_book(request):
    form = forms.IssueBookForm()
    if request.method == "POST":
        form = forms.IssueBookForm(request.POST)
        if form.is_valid():
            obj = models.IssuedBook()
            obj.student_id = request.POST.get('name2')
            obj.isbn = request.POST.get('isbn2')
            obj.save()
            return render(request, "staff_template/issue_book.html", {'obj': obj, 'alert': True, 'form': form})
    return render(request, "staff_template/issue_book.html", {'form': form, 'page_title': 'Issue Book'})


def view_issued_book(request):
    issuedBooks = IssuedBook.objects.all()
    details = []
    for i in issuedBooks:
        days = (date.today() - i.issued_date).days
        fine = (days - 14) * 5 if days > 14 else 0
        books = list(Book.objects.filter(isbn=i.isbn))
        for b in books:
            details.append((b.name, b.isbn, i.issued_date, i.expiry_date, fine))
    return render(request, "staff_template/view_issued_book.html", {'issuedBooks': issuedBooks, 'details': details, 'page_title': 'Issued Books'})
