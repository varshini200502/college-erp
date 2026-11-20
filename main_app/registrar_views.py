"""
Registrar Management Views (Phase 1 & Phase 4)
Handles official institutional onboarding, student/faculty directories,
academic structure management, designations, HOD appointments, and strict role separation.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.db.models import Q

from .models import (
    CustomUser, Staff, Student, Department, Programme, Batch, Section,
    HODAppointment, FacultyProgrammeAffiliation, Registrar, Course, Session
)
from .decorators import registrar_required


@registrar_required
def registrar_home(request):
    """Registrar administrative dashboard with real-time institutional metrics."""
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='Active').count()
    alumni_students = Student.objects.filter(status='Alumni').count()
    graduated_students = Student.objects.filter(status='Graduated').count()
    
    total_faculty = Staff.objects.count()
    active_faculty = Staff.objects.filter(employment_status='Active').count()
    
    total_departments = Department.objects.count()
    total_programmes = Programme.objects.count()
    total_batches = Batch.objects.count()
    total_sections = Section.objects.count()
    
    active_hods = HODAppointment.objects.filter(is_active=True).select_related('faculty__admin', 'department')
    recent_students = Student.objects.select_related('admin', 'course', 'programme').order_by('-id')[:5]
    recent_faculty = Staff.objects.select_related('admin', 'primary_department', 'course').order_by('-id')[:5]

    context = {
        'page_title': 'Office of the Registrar — Institutional Administration',
        'total_students': total_students,
        'active_students': active_students,
        'alumni_students': alumni_students,
        'graduated_students': graduated_students,
        'total_faculty': total_faculty,
        'active_faculty': active_faculty,
        'total_departments': total_departments,
        'total_programmes': total_programmes,
        'total_batches': total_batches,
        'total_sections': total_sections,
        'active_hods': active_hods,
        'recent_students': recent_students,
        'recent_faculty': recent_faculty,
    }
    return render(request, 'registrar_template/home_content.html', context)


@registrar_required
def registrar_student_directory(request):
    """
    Institution-wide Student Directory for the Registrar.
    Displays all enrolled students (24 total) with status-filtering tabs (Active 17, Alumni 6, Graduated 1).
    """
    status_filter = request.GET.get('status', '')
    course_filter = request.GET.get('course', '')
    prog_filter = request.GET.get('programme', '')
    search_query = request.GET.get('search', '').strip()

    students = Student.objects.select_related('admin', 'course', 'programme', 'batch', 'academic_section').all()

    # Total counts for tabs
    total_count = Student.objects.count()
    active_count = Student.objects.filter(status='Active').count()
    alumni_count = Student.objects.filter(status='Alumni').count()
    graduated_count = Student.objects.filter(status='Graduated').count()

    if status_filter:
        students = students.filter(status=status_filter)
    if course_filter:
        students = students.filter(course_id=course_filter)
    if prog_filter:
        students = students.filter(programme_id=prog_filter)
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
    programmes = Programme.objects.filter(is_active=True)

    context = {
        'page_title': 'Registrar Student Directory',
        'students': page_obj,
        'courses': courses,
        'programmes': programmes,
        'selected_status': status_filter,
        'selected_course': course_filter,
        'selected_programme': prog_filter,
        'search_query': search_query,
        'total_count': total_count,
        'active_count': active_count,
        'alumni_count': alumni_count,
        'graduated_count': graduated_count,
    }
    return render(request, 'registrar_template/student_directory.html', context)


@registrar_required
def registrar_faculty_directory(request):
    """
    Institution-wide Faculty Directory for the Registrar.
    Displays faculty appointment details, primary department, designation, and status.
    """
    dept_filter = request.GET.get('department', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '').strip()

    faculty_list = Staff.objects.select_related('admin', 'primary_department', 'course').all()

    total_count = Staff.objects.count()
    active_count = Staff.objects.filter(employment_status='Active').count()

    if dept_filter:
        faculty_list = faculty_list.filter(Q(primary_department_id=dept_filter) | Q(course_id=dept_filter))
    if status_filter:
        faculty_list = faculty_list.filter(employment_status=status_filter)
    if search_query:
        faculty_list = faculty_list.filter(
            Q(admin__first_name__icontains=search_query) |
            Q(admin__last_name__icontains=search_query) |
            Q(admin__email__icontains=search_query) |
            Q(faculty_id__icontains=search_query)
        )

    faculty_list = faculty_list.order_by('id')
    departments = Department.objects.filter(is_active=True)

    context = {
        'page_title': 'Registrar Faculty Directory',
        'faculty_list': faculty_list,
        'departments': departments,
        'selected_dept': dept_filter,
        'selected_status': status_filter,
        'search_query': search_query,
        'total_count': total_count,
        'active_count': active_count,
    }
    return render(request, 'registrar_template/faculty_directory.html', context)


@registrar_required
def registrar_add_student(request):
    """
    Official Academic Onboarding: Create student account and assign
    admission number, department, programme, batch, and section.
    """
    departments = Department.objects.filter(is_active=True)
    programmes = Programme.objects.filter(is_active=True)
    batches = Batch.objects.filter(is_active=True)
    courses = Course.objects.all()
    sessions = Session.objects.all()

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        gender = request.POST.get('gender', 'M')
        password = request.POST.get('password', '').strip()
        address = request.POST.get('address', '').strip()
        course_id = request.POST.get('course')
        programme_id = request.POST.get('programme')
        batch_id = request.POST.get('batch')
        session_id = request.POST.get('session')
        roll_number = request.POST.get('roll_number', '').strip()
        admission_number = request.POST.get('admission_number', '').strip()
        phone = request.POST.get('phone', '').strip()
        parent_name = request.POST.get('parent_name', '').strip()
        parent_phone = request.POST.get('parent_phone', '').strip()
        current_semester = request.POST.get('current_semester') or 1
        section_name = request.POST.get('section', 'A')

        if not email or not password or not first_name or not last_name:
            messages.error(request, "Name, Email, and Password are required fields.")
            return redirect(reverse('registrar_add_student'))

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, f"User with email '{email}' already exists.")
            return redirect(reverse('registrar_add_student'))

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
                profile_pic=passport_url
            )
            user.gender = gender
            user.address = address
            user.save()

            student = user.student
            if course_id:
                student.course = Course.objects.filter(id=course_id).first()
            if programme_id:
                prog = Programme.objects.filter(id=programme_id).first()
                student.programme = prog
                if not student.course and prog:
                    # Link to corresponding course if matching
                    matching_course = Course.objects.filter(name__icontains=prog.name).first()
                    if matching_course:
                        student.course = matching_course
            if batch_id:
                student.batch = Batch.objects.filter(id=batch_id).first()
            if session_id:
                student.session = Session.objects.filter(id=session_id).first()

            student.roll_number = roll_number or f"R-{timezone.now().year}-{user.id}"
            student.admission_number = admission_number or f"ADM-{timezone.now().year}-{user.id}"
            student.phone = phone
            student.parent_name = parent_name
            student.parent_phone = parent_phone
            student.current_semester = int(current_semester)
            student.section = section_name
            student.status = 'Active'
            student.save()

            messages.success(request, f"Student {first_name} {last_name} successfully enrolled (ID: {student.admission_number}).")
            return redirect(reverse('registrar_student_directory'))

        except Exception as e:
            messages.error(request, f"Failed to register student: {str(e)}")
            return redirect(reverse('registrar_add_student'))

    context = {
        'page_title': 'Registrar Onboarding — Add Student',
        'departments': departments,
        'programmes': programmes,
        'batches': batches,
        'courses': courses,
        'sessions': sessions,
    }
    return render(request, 'registrar_template/add_student.html', context)


@registrar_required
def registrar_add_faculty(request):
    """
    Official Academic Onboarding: Create faculty account, assign faculty ID,
    designation, primary department, and employment details.
    """
    departments = Department.objects.filter(is_active=True)
    courses = Course.objects.all()

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        gender = request.POST.get('gender', 'M')
        password = request.POST.get('password', '').strip()
        address = request.POST.get('address', '').strip()
        department_id = request.POST.get('department')
        course_id = request.POST.get('course')
        faculty_id = request.POST.get('faculty_id', '').strip()
        designation = request.POST.get('designation', 'Assistant Professor')
        date_of_joining = request.POST.get('date_of_joining') or timezone.now().date()
        highest_qualification = request.POST.get('highest_qualification', 'Ph.D.')
        specialization = request.POST.get('specialization', '').strip()
        experience = request.POST.get('total_experience_years') or 0.0

        if not email or not password or not first_name or not last_name:
            messages.error(request, "Name, Email, and Password are required.")
            return redirect(reverse('registrar_add_faculty'))

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, f"User with email '{email}' already exists.")
            return redirect(reverse('registrar_add_faculty'))

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
                profile_pic=passport_url
            )
            user.gender = gender
            user.address = address
            user.save()

            staff = user.staff
            if department_id:
                dept = Department.objects.filter(id=department_id).first()
                staff.primary_department = dept
                staff.department = dept.name if dept else ''
            if course_id:
                staff.course = Course.objects.filter(id=course_id).first()

            staff.faculty_id = faculty_id or f"FAC-{timezone.now().year}-{user.id}"
            staff.designation = designation
            staff.date_of_joining = date_of_joining
            staff.highest_qualification = highest_qualification
            staff.specialization = specialization
            staff.total_experience_years = float(experience)
            staff.employment_status = 'Active'
            staff.save()

            messages.success(request, f"Faculty {first_name} {last_name} successfully appointed (ID: {staff.faculty_id}).")
            return redirect(reverse('registrar_faculty_directory'))

        except Exception as e:
            messages.error(request, f"Failed to onboard faculty: {str(e)}")
            return redirect(reverse('registrar_add_faculty'))

    context = {
        'page_title': 'Registrar Onboarding — Add Faculty',
        'departments': departments,
        'courses': courses,
    }
    return render(request, 'registrar_template/add_faculty.html', context)


@registrar_required
def registrar_manage_departments(request):
    """Department Management: View, create, and update Academic/Allied departments."""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        name = request.POST.get('name', '').strip()
        dept_type = request.POST.get('dept_type', 'Academic')
        description = request.POST.get('description', '').strip()

        if code and name:
            if Department.objects.filter(code=code).exists():
                messages.error(request, f"Department code '{code}' already exists.")
            else:
                Department.objects.create(
                    code=code, name=name, dept_type=dept_type, description=description
                )
                messages.success(request, f"Department '{name}' ({code}) successfully registered.")
                return redirect(reverse('registrar_manage_departments'))
        else:
            messages.error(request, "Code and Name are required.")

    departments = Department.objects.all().prefetch_related('programmes', 'hod_appointments')
    context = {
        'page_title': 'Academic Structure — Department Management',
        'departments': departments,
    }
    return render(request, 'registrar_template/manage_departments.html', context)


@registrar_required
def registrar_manage_programmes(request):
    """Programme Management: View, create degree programmes under departments."""
    departments = Department.objects.filter(is_active=True)

    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        name = request.POST.get('name', '').strip()
        dept_id = request.POST.get('department')
        degree_level = request.POST.get('degree_level', 'UG')
        duration = request.POST.get('duration_years') or 4
        nba_status = request.POST.get('nba_status', 'Eligible')

        if code and name and dept_id:
            dept = get_object_or_404(Department, id=dept_id)
            if Programme.objects.filter(code=code).exists():
                messages.error(request, f"Programme code '{code}' already exists.")
            else:
                Programme.objects.create(
                    code=code, name=name, department=dept,
                    degree_level=degree_level, duration_years=int(duration),
                    total_semesters=int(duration) * 2, nba_status=nba_status
                )
                messages.success(request, f"Programme '{name}' ({code}) registered under {dept.name}.")
                return redirect(reverse('registrar_manage_programmes'))
        else:
            messages.error(request, "All fields are required.")

    programmes = Programme.objects.select_related('department').all()
    context = {
        'page_title': 'Academic Structure — Degree Programmes',
        'programmes': programmes,
        'departments': departments,
    }
    return render(request, 'registrar_template/manage_programmes.html', context)


@registrar_required
def registrar_manage_batches(request):
    """Batch and Section Management: View, create batches and sections."""
    programmes = Programme.objects.filter(is_active=True)
    batches = Batch.objects.select_related('programme').prefetch_related('sections').all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_batch':
            prog_id = request.POST.get('programme')
            batch_name = request.POST.get('batch_name', '').strip()
            admission_year = request.POST.get('admission_year')
            graduating_year = request.POST.get('graduating_year')

            if prog_id and batch_name and admission_year and graduating_year:
                prog = get_object_or_404(Programme, id=prog_id)
                Batch.objects.get_or_create(
                    programme=prog, admission_year=int(admission_year),
                    defaults={'batch_name': batch_name, 'graduating_year': int(graduating_year)}
                )
                messages.success(request, f"Batch '{batch_name}' created for {prog.code}.")
                return redirect(reverse('registrar_manage_batches'))

        elif action == 'add_section':
            batch_id = request.POST.get('batch')
            name = request.POST.get('name', 'A').strip().upper()
            semester = request.POST.get('semester') or 1
            academic_year = request.POST.get('academic_year', '2024-2025').strip()

            if batch_id and name:
                batch = get_object_or_404(Batch, id=batch_id)
                Section.objects.get_or_create(
                    batch=batch, name=name, semester=int(semester), academic_year=academic_year
                )
                messages.success(request, f"Section '{name}' (Sem {semester}) added to {batch}.")
                return redirect(reverse('registrar_manage_batches'))

    context = {
        'page_title': 'Academic Structure — Batches & Sections',
        'batches': batches,
        'programmes': programmes,
    }
    return render(request, 'registrar_template/manage_batches.html', context)


@registrar_required
def registrar_academic_structure(request):
    """Comprehensive institutional overview of Academic & Allied departments, programmes, batches."""
    departments = Department.objects.prefetch_related('programmes__batches__sections', 'hod_appointments').all()
    context = {
        'page_title': 'Institutional Academic Structure',
        'departments': departments,
    }
    return render(request, 'registrar_template/academic_structure.html', context)


@registrar_required
def registrar_appoint_hod(request):
    """
    Registrar view to appoint a faculty member as HOD of a department.
    Ensures faculty retains user_type=2 and existing teaching assignments.
    """
    departments = Department.objects.filter(is_active=True)
    faculty_list = Staff.objects.filter(employment_status='Active').select_related('admin', 'primary_department')
    active_appointments = HODAppointment.objects.filter(is_active=True).select_related('faculty__admin', 'department')
    past_appointments = HODAppointment.objects.filter(is_active=False).select_related('faculty__admin', 'department').order_by('-end_date')[:10]

    if request.method == 'POST':
        faculty_id = request.POST.get('faculty_id')
        department_id = request.POST.get('department_id')
        order_no = request.POST.get('order_no', '').strip()
        start_date = request.POST.get('start_date') or timezone.now().date()

        if not faculty_id or not department_id:
            messages.error(request, "Please select both a faculty member and a department.")
            return redirect(reverse('registrar_appoint_hod'))

        faculty = get_object_or_404(Staff, id=faculty_id)
        dept = get_object_or_404(Department, id=department_id)

        # Deactivate any previous active appointment for this department
        HODAppointment.objects.filter(department=dept, is_active=True).update(is_active=False, end_date=timezone.now().date())

        # Create new HOD appointment
        HODAppointment.objects.create(
            faculty=faculty,
            department=dept,
            appointed_by=request.user,
            appointment_order_no=order_no or f"ORD/{dept.code}/HOD/{timezone.now().year}",
            start_date=start_date,
            is_active=True
        )

        messages.success(request, f"Official Appointment Order recorded: {faculty} appointed HOD of {dept.name}.")
        return redirect(reverse('registrar_appoint_hod'))

    context = {
        'page_title': 'Appoint Department Head (HOD)',
        'departments': departments,
        'faculty_list': faculty_list,
        'active_appointments': active_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'registrar_template/appoint_hod.html', context)
