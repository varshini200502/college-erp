from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from datetime import date

from .models import (
    CustomUser, Staff, Course, EmployeeRecord, LeaveQuota,
    LeaveReportStaff, LeaveReportStudent, RecruitmentRecord,
    FacultyTraining, SystemAuditLog
)
from .decorators import role_required


@role_required(['6', '4', '1'])
def hr_home(request):
    """
    HR Dashboard overview.
    """
    total_staff = Staff.objects.count()
    active_staff = Staff.objects.filter(employment_status='Active').count()
    on_leave_staff = Staff.objects.filter(employment_status='On Leave').count()

    pending_staff_leaves = LeaveReportStaff.objects.filter(status=0).count()
    pending_student_leaves = LeaveReportStudent.objects.filter(status=0).count()

    total_recruitments = RecruitmentRecord.objects.count()
    open_positions = RecruitmentRecord.objects.filter(status__in=['Applied', 'Shortlisted', 'Interviewed']).count()

    recent_leaves = LeaveReportStaff.objects.order_by('-created_at')[:6]
    recent_applicants = RecruitmentRecord.objects.order_by('-application_date')[:6]

    context = {
        'page_title': 'HR Management Dashboard',
        'total_staff': total_staff,
        'active_staff': active_staff,
        'on_leave_staff': on_leave_staff,
        'pending_staff_leaves': pending_staff_leaves,
        'pending_student_leaves': pending_student_leaves,
        'total_recruitments': total_recruitments,
        'open_positions': open_positions,
        'recent_leaves': recent_leaves,
        'recent_applicants': recent_applicants,
    }
    return render(request, 'hr_template/hr_home.html', context)


# ==============================================================================
# EMPLOYEE DIRECTORY & RECORDS
# ==============================================================================

@role_required(['6', '4', '1'])
def employee_list(request):
    staff_members = Staff.objects.select_related('admin', 'course').all()
    courses = Course.objects.all()

    dept_filter = request.GET.get('course', '')
    status_filter = request.GET.get('status', '')

    if dept_filter:
        staff_members = staff_members.filter(course_id=dept_filter)
    if status_filter:
        staff_members = staff_members.filter(employment_status=status_filter)

    # Sync EmployeeRecord for all staff members if not present
    for s in staff_members:
        if not hasattr(s.admin, 'employee_record'):
            emp_id = s.faculty_id if s.faculty_id else f"EMP-{s.admin.id:04d}"
            EmployeeRecord.objects.get_or_create(
                user=s.admin,
                defaults={
                    'employee_id': emp_id,
                    'date_of_joining': s.date_of_joining,
                    'employment_type': 'Permanent',
                    'service_status': 'In Service',
                }
            )

    context = {
        'page_title': 'Employee Master Directory',
        'staff_members': staff_members,
        'courses': courses,
        'selected_dept': dept_filter,
        'selected_status': status_filter,
    }
    return render(request, 'hr_template/employee_list.html', context)


@role_required(['6', '4', '1'])
def employee_detail(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    emp_record, _ = EmployeeRecord.objects.get_or_create(
        user=staff.admin,
        defaults={'employee_id': f"EMP-{staff.admin.id:04d}"}
    )
    leave_quota, _ = LeaveQuota.objects.get_or_create(
        user=staff.admin, academic_year="2024-2025"
    )
    leaves = LeaveReportStaff.objects.filter(staff=staff).order_by('-created_at')
    trainings = staff.trainings.all().order_by('-start_date')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_record':
            emp_record.pan_number = request.POST.get('pan_number')
            emp_record.aadhaar_number = request.POST.get('aadhaar_number')
            emp_record.employment_type = request.POST.get('employment_type', 'Permanent')
            emp_record.service_status = request.POST.get('service_status', 'In Service')
            joining = request.POST.get('date_of_joining')
            if joining:
                emp_record.date_of_joining = joining
                staff.date_of_joining = joining
            emp_record.save()

            staff.designation = request.POST.get('designation', staff.designation)
            staff.employment_status = request.POST.get('employment_status', staff.employment_status)
            staff.total_experience_years = float(request.POST.get('total_experience_years') or staff.total_experience_years)
            staff.highest_qualification = request.POST.get('highest_qualification', staff.highest_qualification)
            staff.specialization = request.POST.get('specialization', staff.specialization)
            staff.save()

            SystemAuditLog.objects.create(
                user=request.user,
                action="UPDATE",
                module="HR",
                description=f"Updated employee master record for {staff.admin.email}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Employee record for {staff} updated successfully!")
            return redirect(reverse('employee_detail', args=[staff.id]))

    context = {
        'page_title': f'Employee Record - {staff}',
        'staff': staff,
        'emp_record': emp_record,
        'leave_quota': leave_quota,
        'leaves': leaves,
        'trainings': trainings,
    }
    return render(request, 'hr_template/employee_detail.html', context)


# ==============================================================================
# LEAVE MANAGEMENT & APPROVALS
# ==============================================================================

@role_required(['6', '4', '1'])
def hr_leave_management(request):
    staff_leaves = LeaveReportStaff.objects.select_related('staff__admin').order_by('-created_at')
    student_leaves = LeaveReportStudent.objects.select_related('student__admin').order_by('-created_at')

    status_filter = request.GET.get('status', '0')  # Default show pending
    if status_filter != 'all':
        staff_leaves = staff_leaves.filter(status=int(status_filter))
        student_leaves = student_leaves.filter(status=int(status_filter))

    if request.method == 'POST':
        leave_type = request.POST.get('leave_type')
        leave_id = request.POST.get('leave_id')
        decision = int(request.POST.get('decision'))  # 1 for approved, 2 for rejected

        if leave_type == 'staff':
            leave = get_object_or_404(LeaveReportStaff, id=leave_id)
            leave.status = decision
            leave.save()

            # Update leave balance if approved
            if decision == 1:
                quota = LeaveQuota.objects.filter(user=leave.staff.admin, academic_year="2024-2025").first()
                if quota:
                    quota.casual_leave_taken += 1
                    quota.save()

            status_str = "Approved" if decision == 1 else "Rejected"
            SystemAuditLog.objects.create(
                user=request.user,
                action="LEAVE_DECISION",
                module="HR",
                description=f"{status_str} staff leave request for {leave.staff} (Date: {leave.date})",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Staff leave request {status_str.lower()}.")
            return redirect(reverse('hr_leave_management'))

        elif leave_type == 'student':
            leave = get_object_or_404(LeaveReportStudent, id=leave_id)
            leave.status = decision
            leave.save()
            status_str = "Approved" if decision == 1 else "Rejected"
            messages.success(request, f"Student leave request {status_str.lower()}.")
            return redirect(reverse('hr_leave_management'))

    context = {
        'page_title': 'Institutional Leave Management',
        'staff_leaves': staff_leaves,
        'student_leaves': student_leaves,
        'selected_status': status_filter,
    }
    return render(request, 'hr_template/leave_management.html', context)


# ==============================================================================
# RECRUITMENT & TALENT MANAGEMENT
# ==============================================================================

@role_required(['6', '4', '1'])
def recruitment_list(request):
    recruitments = RecruitmentRecord.objects.select_related('department').order_by('-application_date')
    courses = Course.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_applicant':
            dept_id = request.POST.get('department')
            pos = request.POST.get('position')
            name = request.POST.get('applicant_name')
            email = request.POST.get('applicant_email')
            phone = request.POST.get('applicant_phone')
            notes = request.POST.get('notes', '')
            resume = request.FILES.get('resume')

            dept = get_object_or_404(Course, id=dept_id)
            RecruitmentRecord.objects.create(
                department=dept,
                position=pos,
                applicant_name=name,
                applicant_email=email,
                applicant_phone=phone,
                notes=notes,
                resume=resume,
            )
            SystemAuditLog.objects.create(
                user=request.user,
                action="RECRUITMENT",
                module="HR",
                description=f"Added applicant {name} for position {pos} in {dept.name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Candidate '{name}' registered successfully.")
            return redirect(reverse('recruitment_list'))

        elif action == 'update_status':
            rec_id = request.POST.get('recruitment_id')
            new_status = request.POST.get('status')
            rec = get_object_or_404(RecruitmentRecord, id=rec_id)
            rec.status = new_status
            rec.save()

            messages.success(request, f"Status for '{rec.applicant_name}' updated to {new_status}.")
            return redirect(reverse('recruitment_list'))

    context = {
        'page_title': 'Recruitment & Onboarding Portal',
        'recruitments': recruitments,
        'courses': courses,
    }
    return render(request, 'hr_template/recruitment_list.html', context)
