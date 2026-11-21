import json
import requests
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.db import models as django_models
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView

from .forms import *
from .models import *
from .decorators import role_required


@role_required(['1'])
def admin_home(request):
    total_staff = Staff.objects.all().count()
    total_students = Student.objects.all().count()
    total_course = Course.objects.all().count()
    total_subject = Subject.objects.all().count()

    # Subjects with attendance count (1 bulk group-by query instead of N queries)
    subjects = list(Subject.objects.select_related('course').all().order_by('id'))
    att_counts = dict(Attendance.objects.values('subject_id').annotate(c=Count('id')).values_list('subject_id', 'c'))
    attendance_list = [att_counts.get(s.id, 0) for s in subjects]

    # Courses with subject and student counts (2 bulk group-by queries instead of 2*N queries)
    course_all = list(Course.objects.all().order_by('id'))
    courses_stu_counts = dict(Student.objects.values('course_id').annotate(c=Count('id')).values_list('course_id', 'c'))
    courses_sub_counts = dict(Subject.objects.values('course_id').annotate(c=Count('id')).values_list('course_id', 'c'))

    course_name_list = [c.name for c in course_all]
    subject_count_list = [courses_sub_counts.get(c.id, 0) for c in course_all]
    student_count_list_in_course = [courses_stu_counts.get(c.id, 0) for c in course_all]

    subject_list = [s.name for s in subjects]
    student_count_list_in_subject = [courses_stu_counts.get(s.course_id, 0) for s in subjects]

    # Students attendance present/absent/leave (3 bulk queries + select_related instead of 4*N queries)
    students = list(Student.objects.select_related('admin').all().order_by('id'))
    att_present = dict(AttendanceReport.objects.filter(status=True).values('student_id').annotate(c=Count('id')).values_list('student_id', 'c'))
    att_absent = dict(AttendanceReport.objects.filter(status=False).values('student_id').annotate(c=Count('id')).values_list('student_id', 'c'))
    leave_counts = dict(LeaveReportStudent.objects.filter(status=1).values('student_id').annotate(c=Count('id')).values_list('student_id', 'c'))

    student_attendance_present_list = []
    student_attendance_leave_list = []
    student_name_list = []
    for student in students:
        pres = att_present.get(student.id, 0)
        absn = att_absent.get(student.id, 0)
        lv = leave_counts.get(student.id, 0)
        student_attendance_present_list.append(pres)
        student_attendance_leave_list.append(lv + absn)
        student_name_list.append(student.admin.first_name if student.admin else 'Unknown')

    context = {
        'page_title': "Administrative Dashboard",
        'total_students': total_students,
        'total_staff': total_staff,
        'total_course': total_course,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list,
        'student_attendance_present_list': student_attendance_present_list,
        'student_attendance_leave_list': student_attendance_leave_list,
        "student_name_list": student_name_list,
        "student_count_list_in_subject": student_count_list_in_subject,
        "student_count_list_in_course": student_count_list_in_course,
        "course_name_list": course_name_list,

    }
    return render(request, 'hod_template/home_content.html', context)


@role_required(['8', '4'])
def add_staff(request):
    form = StaffForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Add Staff'}
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            course = form.cleaned_data.get('course')
            # Extended staff fields
            faculty_id = form.cleaned_data.get('faculty_id') or ''
            designation = form.cleaned_data.get('designation') or 'Assistant Professor'
            department = form.cleaned_data.get('department') or ''
            date_of_joining = form.cleaned_data.get('date_of_joining')
            employment_status = form.cleaned_data.get('employment_status') or 'Active'
            total_experience_years = form.cleaned_data.get('total_experience_years') or 0.0
            highest_qualification = form.cleaned_data.get('highest_qualification') or ''
            specialization = form.cleaned_data.get('specialization') or ''

            passport = request.FILES.get('profile_pic')
            passport_url = ''
            if passport:
                try:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                except Exception:
                    passport_url = ''
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=2,
                    first_name=first_name, last_name=last_name,
                    profile_pic=passport_url)
                user.gender = gender
                user.address = address
                user.save()
                # Update the auto-created Staff profile
                staff_obj = user.staff
                staff_obj.course = course
                staff_obj.faculty_id = faculty_id
                staff_obj.designation = designation
                staff_obj.department = department
                if date_of_joining:
                    staff_obj.date_of_joining = date_of_joining
                staff_obj.employment_status = employment_status
                staff_obj.total_experience_years = total_experience_years
                staff_obj.highest_qualification = highest_qualification
                staff_obj.specialization = specialization
                staff_obj.save()
                messages.success(request, f"Faculty '{first_name} {last_name}' added successfully!")
                return redirect(reverse('add_staff'))

            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Please fulfil all required fields correctly.")

    return render(request, 'hod_template/add_staff_template.html', context)


@role_required(['8', '4'])
def add_student(request):
    student_form = StudentForm(request.POST or None, request.FILES or None)
    context = {'form': student_form, 'page_title': 'Add Student'}
    if request.method == 'POST':
        if student_form.is_valid():
            first_name = student_form.cleaned_data.get('first_name')
            last_name = student_form.cleaned_data.get('last_name')
            address = student_form.cleaned_data.get('address')
            email = student_form.cleaned_data.get('email')
            gender = student_form.cleaned_data.get('gender')
            password = student_form.cleaned_data.get('password')
            course = student_form.cleaned_data.get('course')
            session = student_form.cleaned_data.get('session')
            # Extended student fields
            roll_number = student_form.cleaned_data.get('roll_number') or ''
            admission_number = student_form.cleaned_data.get('admission_number') or ''
            date_of_birth = student_form.cleaned_data.get('date_of_birth')
            phone = student_form.cleaned_data.get('phone') or ''
            parent_name = student_form.cleaned_data.get('parent_name') or ''
            parent_phone = student_form.cleaned_data.get('parent_phone') or ''
            current_semester = student_form.cleaned_data.get('current_semester') or 1
            section = student_form.cleaned_data.get('section') or 'A'
            status = student_form.cleaned_data.get('status') or 'Active'

            passport = request.FILES.get('profile_pic')
            passport_url = ''
            if passport:
                try:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                except Exception:
                    passport_url = ''
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=3,
                    first_name=first_name, last_name=last_name,
                    profile_pic=passport_url)
                user.gender = gender
                user.address = address
                user.save()
                # Update the auto-created Student profile
                student_obj = user.student
                student_obj.session = session
                student_obj.course = course
                student_obj.roll_number = roll_number
                student_obj.admission_number = admission_number
                if date_of_birth:
                    student_obj.date_of_birth = date_of_birth
                student_obj.phone = phone
                student_obj.parent_name = parent_name
                student_obj.parent_phone = parent_phone
                student_obj.current_semester = current_semester
                student_obj.section = section
                student_obj.status = status
                student_obj.save()
                messages.success(request, f"Student '{first_name} {last_name}' added successfully!")
                return redirect(reverse('add_student'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Please fill all required fields correctly.")
    return render(request, 'hod_template/add_student_template.html', context)


@role_required(['1', '4', '8'])
def add_course(request):
    form = CourseForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Course'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                course = Course()
                course.name = name
                course.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_course'))
            except:
                messages.error(request, "Could Not Add")
        else:
            messages.error(request, "Could Not Add")
    return render(request, 'hod_template/add_course_template.html', context)


@role_required(['1', '4', '8'])
def add_subject(request):
    form = SubjectForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            try:
                subject = Subject()
                subject.name = name
                subject.staff = staff
                subject.course = course
                subject.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_subject'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/add_subject_template.html', context)


@role_required(['8', '4'])
def manage_staff(request):
    query = request.GET.get('q', '')
    course_filter = request.GET.get('course', '')
    status_filter = request.GET.get('status', '')

    allStaff = CustomUser.objects.filter(user_type=2).select_related('staff', 'staff__course')
    if query:
        allStaff = allStaff.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(staff__faculty_id__icontains=query)
        )
    if course_filter:
        allStaff = allStaff.filter(staff__course__id=course_filter)
    if status_filter:
        allStaff = allStaff.filter(staff__employment_status=status_filter)

    courses = Course.objects.all()
    context = {
        'allStaff': allStaff,
        'courses': courses,
        'page_title': 'Manage Faculty',
        'query': query,
        'course_filter': course_filter,
        'status_filter': status_filter,
        'employment_statuses': Staff.EMPLOYMENT_STATUS,
    }
    return render(request, "hod_template/manage_staff.html", context)


@role_required(['8', '4'])
def manage_student(request):
    query = request.GET.get('q', '')
    course_filter = request.GET.get('course', '')
    session_filter = request.GET.get('session', '')
    status_filter = request.GET.get('status', '')
    semester_filter = request.GET.get('semester', '')

    students = CustomUser.objects.filter(user_type=3).select_related('student', 'student__course', 'student__session')
    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(student__roll_number__icontains=query) |
            Q(student__admission_number__icontains=query)
        )
    if course_filter:
        students = students.filter(student__course__id=course_filter)
    if session_filter:
        students = students.filter(student__session__id=session_filter)
    if status_filter:
        students = students.filter(student__status=status_filter)
    if semester_filter:
        students = students.filter(student__current_semester=semester_filter)

    courses = Course.objects.all()
    sessions = Session.objects.all()
    context = {
        'students': students,
        'courses': courses,
        'sessions': sessions,
        'page_title': 'Manage Students',
        'query': query,
        'course_filter': course_filter,
        'session_filter': session_filter,
        'status_filter': status_filter,
        'semester_filter': semester_filter,
        'status_choices': Student.STATUS_CHOICES,
        'semesters': range(1, 9),
    }
    return render(request, "hod_template/manage_student.html", context)


@role_required(['1', '4', '8'])
def manage_course(request):
    courses = Course.objects.all()
    context = {
        'courses': courses,
        'page_title': 'Manage Courses'
    }
    return render(request, "hod_template/manage_course.html", context)


@role_required(['1', '4', '8'])
def manage_departments(request):
    departments = Department.objects.prefetch_related('programmes', 'faculty_members', 'hod_appointments__faculty__admin').all()
    context = {
        'departments': departments,
        'page_title': 'Manage Departments'
    }
    return render(request, "hod_template/manage_department.html", context)


@role_required(['1', '4', '7', '8'])
def manage_programmes(request):
    programmes = Programme.objects.select_related('department').prefetch_related('batches', 'students').all()
    context = {
        'programmes': programmes,
        'page_title': 'Manage Academic Programmes'
    }
    return render(request, "hod_template/manage_programme.html", context)


@role_required(['1', '4', '7', '8'])
def manage_regulations(request):
    regulations = AcademicRegulation.objects.select_related('programme').all().order_by('-effective_year')
    context = {
        'regulations': regulations,
        'page_title': 'Institutional Academic Regulations'
    }
    return render(request, "hod_template/manage_regulations.html", context)


@role_required(['2', '4', '7', '8'])
def manage_projects(request):
    projects = StudentProject.objects.select_related('primary_programme', 'secondary_programme', 'guide', 'co_guide').prefetch_related('students__admin').all().order_by('-created_at')
    context = {
        'projects': projects,
        'page_title': 'Capstone & Interdisciplinary Projects'
    }
    return render(request, "hod_template/manage_projects.html", context)


@role_required(['1', '4', '8'])
def manage_subject(request):
    subjects = Subject.objects.all()
    context = {
        'subjects': subjects,
        'page_title': 'Manage Subjects'
    }
    return render(request, "hod_template/manage_subject.html", context)


@role_required(['8', '4'])
def edit_staff(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    form = StaffForm(request.POST or None, instance=staff)
    context = {
        'form': form,
        'staff_id': staff_id,
        'page_title': 'Edit Staff'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            course = form.cleaned_data.get('course')
            # Extended staff fields
            faculty_id = form.cleaned_data.get('faculty_id') or staff.faculty_id
            designation = form.cleaned_data.get('designation') or staff.designation
            department = form.cleaned_data.get('department') or staff.department
            date_of_joining = form.cleaned_data.get('date_of_joining') or staff.date_of_joining
            employment_status = form.cleaned_data.get('employment_status') or staff.employment_status
            total_experience_years = form.cleaned_data.get('total_experience_years')
            highest_qualification = form.cleaned_data.get('highest_qualification') or staff.highest_qualification
            specialization = form.cleaned_data.get('specialization') or staff.specialization

            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=staff.admin.id)
                user.email = email
                if password is not None:
                    user.set_password(password)
                if passport is not None:
                    try:
                        fs = FileSystemStorage()
                        filename = fs.save(passport.name, passport)
                        passport_url = fs.url(filename)
                        user.profile_pic = passport_url
                    except Exception:
                        pass
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                user.save()
                # Save extended staff fields
                staff.course = course
                staff.faculty_id = faculty_id
                staff.designation = designation
                staff.department = department
                if date_of_joining:
                    staff.date_of_joining = date_of_joining
                staff.employment_status = employment_status
                if total_experience_years is not None:
                    staff.total_experience_years = total_experience_years
                staff.highest_qualification = highest_qualification
                staff.specialization = specialization
                staff.save()
                messages.success(request, "Staff profile updated successfully!")
                return redirect(reverse('edit_staff', args=[staff_id]))
            except Exception as e:
                messages.error(request, "Could Not Update: " + str(e))
        else:
            messages.error(request, "Please fill the form properly.")
    return render(request, "hod_template/edit_staff_template.html", context)


@role_required(['8', '4'])
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    form = StudentForm(request.POST or None, instance=student)
    context = {
        'form': form,
        'student_id': student_id,
        'page_title': 'Edit Student'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            course = form.cleaned_data.get('course')
            session = form.cleaned_data.get('session')
            # Extended student fields
            roll_number = form.cleaned_data.get('roll_number') or student.roll_number
            admission_number = form.cleaned_data.get('admission_number') or student.admission_number
            date_of_birth = form.cleaned_data.get('date_of_birth') or student.date_of_birth
            phone = form.cleaned_data.get('phone') or student.phone
            parent_name = form.cleaned_data.get('parent_name') or student.parent_name
            parent_phone = form.cleaned_data.get('parent_phone') or student.parent_phone
            current_semester = form.cleaned_data.get('current_semester') or student.current_semester
            section = form.cleaned_data.get('section') or student.section
            status = form.cleaned_data.get('status') or student.status

            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=student.admin.id)
                if passport is not None:
                    try:
                        fs = FileSystemStorage()
                        filename = fs.save(passport.name, passport)
                        passport_url = fs.url(filename)
                        user.profile_pic = passport_url
                    except Exception:
                        pass
                user.email = email
                if password is not None:
                    user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                user.save()
                # Save extended student fields
                student.session = session
                student.course = course
                student.roll_number = roll_number
                student.admission_number = admission_number
                if date_of_birth:
                    student.date_of_birth = date_of_birth
                student.phone = phone
                student.parent_name = parent_name
                student.parent_phone = parent_phone
                if current_semester:
                    student.current_semester = current_semester
                student.section = section
                student.status = status
                student.save()
                messages.success(request, "Student profile updated successfully!")
                return redirect(reverse('edit_student', args=[student_id]))
            except Exception as e:
                messages.error(request, "Could Not Update: " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly!")
    return render(request, "hod_template/edit_student_template.html", context)


@role_required(['1', '4', '8'])
def edit_course(request, course_id):
    instance = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'course_id': course_id,
        'page_title': 'Edit Course'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                course = Course.objects.get(id=course_id)
                course.name = name
                course.save()
                messages.success(request, "Successfully Updated")
            except:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'hod_template/edit_course_template.html', context)


@role_required(['1', '4', '8'])
def edit_subject(request, subject_id):
    instance = get_object_or_404(Subject, id=subject_id)
    form = SubjectForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'subject_id': subject_id,
        'page_title': 'Edit Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.name = name
                subject.staff = staff
                subject.course = course
                subject.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_subject', args=[subject_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'hod_template/edit_subject_template.html', context)


@role_required(['1', '4', '8'])
def add_session(request):
    form = SessionForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Session'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Created")
                return redirect(reverse('add_session'))
            except Exception as e:
                messages.error(request, 'Could Not Add ' + str(e))
        else:
            messages.error(request, 'Fill Form Properly ')
    return render(request, "hod_template/add_session_template.html", context)


@role_required(['1', '4', '8'])
def manage_session(request):
    sessions = Session.objects.all()
    context = {'sessions': sessions, 'page_title': 'Manage Sessions'}
    return render(request, "hod_template/manage_session.html", context)


@role_required(['1', '4', '8'])
def edit_session(request, session_id):
    instance = get_object_or_404(Session, id=session_id)
    form = SessionForm(request.POST or None, instance=instance)
    context = {'form': form, 'session_id': session_id,
               'page_title': 'Edit Session'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Updated")
                return redirect(reverse('edit_session', args=[session_id]))
            except Exception as e:
                messages.error(
                    request, "Session Could Not Be Updated " + str(e))
                return render(request, "hod_template/edit_session_template.html", context)
        else:
            messages.error(request, "Invalid Form Submitted ")
            return render(request, "hod_template/edit_session_template.html", context)

    else:
        return render(request, "hod_template/edit_session_template.html", context)


@csrf_exempt
def check_email_availability(request):
    email = request.POST.get("email")
    try:
        user = CustomUser.objects.filter(email=email).exists()
        if user:
            return HttpResponse(True)
        return HttpResponse(False)
    except Exception as e:
        return HttpResponse(False)


@csrf_exempt
@role_required(['4', '2'])
def student_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStudent.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Student Feedback Messages'
        }
        return render(request, 'hod_template/student_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStudent, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


@csrf_exempt
@role_required(['4'])
def staff_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStaff.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Staff Feedback Messages'
        }
        return render(request, 'hod_template/staff_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStaff, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


@csrf_exempt
@role_required(['4', '2'])
def view_staff_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportStaff.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Staff'
        }
        return render(request, "hod_template/staff_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStaff, id=id)
            # Separation of duties: A user cannot approve their own leave
            if hasattr(request.user, 'staff') and leave.staff == request.user.staff:
                return HttpResponse("Forbidden: Self-approval of leave is prohibited.", status=403)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


@csrf_exempt
@role_required(['4', '2'])
def view_student_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportStudent.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Students'
        }
        return render(request, "hod_template/student_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStudent, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


@role_required(['1', '4'])
def admin_view_attendance(request):
    subjects = Subject.objects.all()
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'View Attendance'
    }

    return render(request, "hod_template/admin_view_attendance.html", context)


@role_required(['1', '4'])
def get_admin_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = get_object_or_404(
            Attendance, id=attendance_date_id, session=session)
        attendance_reports = AttendanceReport.objects.filter(
            attendance=attendance)
        json_data = []
        for report in attendance_reports:
            data = {
                "status":  str(report.status),
                "name": str(report.student)
            }
            json_data.append(data)
        return JsonResponse(json.dumps(json_data), safe=False)
    except Exception as e:
        return None


@role_required(['1'])
def admin_view_profile(request):
    admin = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None,
                     instance=admin)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                passport = request.FILES.get('profile_pic') or None
                custom_user = admin.admin
                if password != None:
                    custom_user.set_password(password)
                if passport != None:
                    try:
                        fs = FileSystemStorage()
                        filename = fs.save(passport.name, passport)
                        passport_url = fs.url(filename)
                        custom_user.profile_pic = passport_url
                    except Exception:
                        pass
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
    return render(request, "hod_template/admin_view_profile.html", context)


@role_required(['1', '4'])
def admin_notify_staff(request):
    staff = CustomUser.objects.filter(user_type=2)
    context = {
        'page_title': "Send Notifications To Staff",
        'allStaff': staff
    }
    return render(request, "hod_template/staff_notification.html", context)


@role_required(['1', '4'])
def admin_notify_student(request):
    student = CustomUser.objects.filter(user_type=3)
    context = {
        'page_title': "Send Notifications To Students",
        'students': student
    }
    return render(request, "hod_template/student_notification.html", context)


@csrf_exempt
@role_required(['1', '4'])
def send_student_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    student = get_object_or_404(Student, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message,
                'click_action': reverse('student_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': student.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationStudent(student=student, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


@csrf_exempt
@role_required(['1', '4'])
def send_staff_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    staff = get_object_or_404(Staff, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message,
                'click_action': reverse('staff_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': staff.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationStaff(staff=staff, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


@role_required(['8', '4'])
def delete_staff(request, staff_id):
    staff_obj = get_object_or_404(Staff, id=staff_id)
    # Prefer deactivation over destructive deletion to preserve historical institutional records
    staff_obj.employment_status = 'Resigned'
    staff_obj.admin.is_active = False
    staff_obj.admin.save()
    staff_obj.save()
    messages.success(request, f"Staff record for {staff_obj} deactivated (marked Resigned)!")
    return redirect(reverse('manage_staff'))


@role_required(['8', '4'])
def delete_student(request, student_id):
    student_obj = get_object_or_404(Student, id=student_id)
    # Prefer deactivation over destructive deletion to preserve academic/fee records
    student_obj.status = 'Inactive'
    student_obj.admin.is_active = False
    student_obj.admin.save()
    student_obj.save()
    messages.success(request, f"Student record for {student_obj} deactivated (marked Inactive)!")
    return redirect(reverse('manage_student'))


@role_required(['8', '4'])
def toggle_student_status(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    new_status = request.POST.get('status', 'Active')
    student.status = new_status
    if new_status in ['Active']:
        student.admin.is_active = True
    else:
        # Graduated, Alumni, or Inactive
        student.admin.is_active = True if new_status in ['Graduated', 'Alumni'] else False
    student.admin.save()
    student.save()
    messages.success(request, f"Student status for {student} set to {new_status}.")
    return redirect(reverse('manage_student'))


@role_required(['8', '4'])
def toggle_staff_status(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    new_status = request.POST.get('employment_status', 'Active')
    staff.employment_status = new_status
    staff.admin.is_active = (new_status in ['Active', 'On Leave'])
    staff.admin.save()
    staff.save()
    messages.success(request, f"Staff status for {staff} set to {new_status}.")
    return redirect(reverse('manage_staff'))


@role_required(['1', '4', '7'])
def institutional_documents(request):
    documents = InstitutionalDocument.objects.all().order_by('-created_at')
    courses = Course.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload_document':
            title = request.POST.get('title')
            category = request.POST.get('category')
            dept_id = request.POST.get('department')
            acad_year = request.POST.get('academic_year', '2024-2025')
            doc_file = request.FILES.get('file')

            dept = Course.objects.filter(id=dept_id).first() if dept_id else None
            InstitutionalDocument.objects.create(
                title=title,
                category=category,
                department=dept,
                academic_year=acad_year,
                file=doc_file,
                uploaded_by=request.user
            )
            SystemAuditLog.objects.create(
                user=request.user,
                action="DOCUMENT_UPLOAD",
                module="DocumentManagement",
                description=f"Uploaded institutional document: [{category}] {title}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Document '{title}' uploaded successfully!")
            return redirect(reverse('institutional_documents'))

    context = {
        'page_title': 'Institutional Document Repository',
        'documents': documents,
        'courses': courses,
    }
    return render(request, 'hod_template/institutional_documents.html', context)


@role_required(['1', '4', '7'])
def verify_institutional_document(request, doc_id):
    doc = get_object_or_404(InstitutionalDocument, id=doc_id)
    decision = request.POST.get('decision') == 'true'
    doc.is_verified = decision
    doc.verified_by = request.user if decision else None
    doc.save()
    status_str = "Verified" if decision else "Pending Verification"
    messages.success(request, f"Document '{doc.title}' marked as {status_str}.")
    return redirect(reverse('institutional_documents'))


@role_required(['1', '4'])
def system_audit_logs(request):
    logs = SystemAuditLog.objects.all().order_by('-timestamp')[:100]
    context = {
        'page_title': 'System Audit Trails & Security Logs',
        'logs': logs,
    }
    return render(request, 'hod_template/system_audit_logs.html', context)


@role_required(['1', '4', '8'])
def centralized_reports(request):
    total_students = Student.objects.filter(status='Active').count()
    alumni_students = Student.objects.filter(status__in=['Graduated', 'Alumni']).count()
    total_faculty = Staff.objects.filter(employment_status='Active').count()
    courses = Course.objects.all()

    dept_summary = []
    for c in courses:
        s_count = Student.objects.filter(course=c, status='Active').count()
        f_count = Staff.objects.filter(course=c, employment_status='Active').count()
        dept_summary.append({
            'course': c,
            'students': s_count,
            'faculty': f_count,
            'sfr': round(s_count / f_count, 1) if f_count > 0 else 0
        })

    context = {
        'page_title': 'Centralized Institutional Analytics & Reporting',
        'total_students': total_students,
        'alumni_students': alumni_students,
        'total_faculty': total_faculty,
        'dept_summary': dept_summary,
    }
    return render(request, 'hod_template/centralized_reports.html', context)


@role_required(['1', '4', '8'])
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    try:
        course.delete()
        messages.success(request, "Course deleted successfully!")
    except Exception:
        messages.error(
            request, "Sorry, some students are assigned to this course already. Kindly change the affected student course and try again")
    return redirect(reverse('manage_course'))


@role_required(['1', '4', '8'])
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully!")
    return redirect(reverse('manage_subject'))


@role_required(['1', '4', '8'])
def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    try:
        session.delete()
        messages.success(request, "Session deleted successfully!")
    except Exception:
        messages.error(
            request, "There are students assigned to this session. Please move them to another session.")
    return redirect(reverse('manage_session'))



# ============================================================
# ALUMNI MANAGEMENT VIEWS
# ============================================================

@role_required(['8', '4'])
def graduate_student(request, student_id):
    """Mark a student as Graduated and create/update their AlumniProfile."""
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        graduation_year = request.POST.get('graduation_year', 2024)
        degree_awarded = request.POST.get('degree_awarded', 'Bachelor of Technology')
        current_company = request.POST.get('current_company', '')
        current_designation = request.POST.get('current_designation', '')
        current_city = request.POST.get('current_city', '')
        higher_education_institution = request.POST.get('higher_education_institution', '')
        higher_education_degree = request.POST.get('higher_education_degree', '')
        linkedin_url = request.POST.get('linkedin_url', '') or None
        engagement_notes = request.POST.get('engagement_notes', '')
        is_notable = request.POST.get('is_notable') == 'on'

        # Update student status
        student.status = 'Alumni'
        student.admin.is_active = True  # Keep alumni account active for reference
        student.admin.save()
        student.save()

        # Create or update AlumniProfile
        alumni, created = AlumniProfile.objects.get_or_create(student=student)
        alumni.graduation_year = int(graduation_year)
        alumni.degree_awarded = degree_awarded
        alumni.current_company = current_company
        alumni.current_designation = current_designation
        alumni.current_city = current_city
        alumni.higher_education_institution = higher_education_institution
        alumni.higher_education_degree = higher_education_degree
        alumni.linkedin_url = linkedin_url
        alumni.engagement_notes = engagement_notes
        alumni.is_notable = is_notable
        alumni.save()

        SystemAuditLog.objects.create(
            user=request.user,
            action="STUDENT_GRADUATED",
            module="AlumniManagement",
            description=f"Student {student} (ID:{student.id}) graduated. Alumni profile {'created' if created else 'updated'}.",
            ip_address=request.META.get('REMOTE_ADDR')
        )

        action = 'created' if created else 'updated'
        messages.success(request, f"Student '{student}' has been graduated and alumni profile {action}!")
        return redirect(reverse('alumni_list'))
    else:
        # Show graduation form
        context = {
            'student': student,
            'page_title': f'Graduate Student: {student}',
            'current_year': __import__('datetime').date.today().year,
        }
        return render(request, 'hod_template/graduate_student.html', context)


@role_required(['8', '4'])
def alumni_list(request):
    """List all alumni with search and filter."""
    query = request.GET.get('q', '')
    year_filter = request.GET.get('year', '')
    course_filter = request.GET.get('course', '')
    notable_filter = request.GET.get('notable', '')

    alumni_profiles = AlumniProfile.objects.select_related(
        'student', 'student__admin', 'student__course'
    ).order_by('-graduation_year', 'student__admin__last_name')

    if query:
        alumni_profiles = alumni_profiles.filter(
            Q(student__admin__first_name__icontains=query) |
            Q(student__admin__last_name__icontains=query) |
            Q(student__admin__email__icontains=query) |
            Q(current_company__icontains=query) |
            Q(current_designation__icontains=query) |
            Q(student__roll_number__icontains=query)
        )
    if year_filter:
        alumni_profiles = alumni_profiles.filter(graduation_year=year_filter)
    if course_filter:
        alumni_profiles = alumni_profiles.filter(student__course__id=course_filter)
    if notable_filter == '1':
        alumni_profiles = alumni_profiles.filter(is_notable=True)

    # Also show Graduated students without AlumniProfile
    graduated_without_profile = Student.objects.filter(
        status__in=['Graduated', 'Alumni']
    ).exclude(id__in=AlumniProfile.objects.values_list('student__id', flat=True))

    courses = Course.objects.all()
    years = AlumniProfile.objects.values_list('graduation_year', flat=True).distinct().order_by('-graduation_year')

    context = {
        'alumni_profiles': alumni_profiles,
        'graduated_without_profile': graduated_without_profile,
        'courses': courses,
        'years': years,
        'page_title': 'Alumni Management',
        'query': query,
        'year_filter': year_filter,
        'course_filter': course_filter,
        'notable_filter': notable_filter,
        'total_alumni': alumni_profiles.count(),
    }
    return render(request, 'hod_template/alumni_list.html', context)


@role_required(['8', '4'])
def alumni_detail(request, alumni_id):
    """View and update detailed alumni profile."""
    alumni = get_object_or_404(AlumniProfile, id=alumni_id)
    student = alumni.student

    if request.method == 'POST':
        alumni.current_company = request.POST.get('current_company', '')
        alumni.current_designation = request.POST.get('current_designation', '')
        alumni.current_city = request.POST.get('current_city', '')
        alumni.higher_education_institution = request.POST.get('higher_education_institution', '')
        alumni.higher_education_degree = request.POST.get('higher_education_degree', '')
        linkedin_url = request.POST.get('linkedin_url', '') or None
        alumni.linkedin_url = linkedin_url
        alumni.engagement_notes = request.POST.get('engagement_notes', '')
        alumni.is_notable = request.POST.get('is_notable') == 'on'
        alumni.degree_awarded = request.POST.get('degree_awarded', alumni.degree_awarded)
        try:
            alumni.graduation_year = int(request.POST.get('graduation_year', alumni.graduation_year))
        except (ValueError, TypeError):
            pass
        alumni.save()
        messages.success(request, "Alumni profile updated successfully!")
        return redirect(reverse('alumni_detail', args=[alumni_id]))

    # Gather academic history from StudentResult
    results = StudentResult.objects.filter(student=student).select_related('subject')
    # Attendance summary
    attendance_reports = AttendanceReport.objects.filter(student=student)
    total_classes = attendance_reports.count()
    present_classes = attendance_reports.filter(status=True).count()
    attendance_pct = round((present_classes / total_classes * 100), 1) if total_classes > 0 else 0

    context = {
        'alumni': alumni,
        'student': student,
        'results': results,
        'total_classes': total_classes,
        'present_classes': present_classes,
        'attendance_pct': attendance_pct,
        'page_title': f'Alumni Profile: {student}',
        'current_year': __import__('datetime').date.today().year,
    }
    return render(request, 'hod_template/alumni_detail.html', context)
