from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.db.models import Sum, Count, Q
from datetime import date
import uuid

from .models import (
    CustomUser, Course, Session, Student,
    FeeStructure, StudentFeeAccount, FeePayment,
    Payroll, CollegeExpense, DepartmentBudget, SystemAuditLog
)
from .decorators import role_required
from .pdf_generator import SimplePDF


@role_required(['5', '4', '1'])
def finance_home(request):
    """
    Finance Dashboard overview.
    """
    total_fee_collected = FeePayment.objects.filter(is_refunded=False).aggregate(s=Sum('amount_paid'))['s'] or 0.0
    total_fee_due = StudentFeeAccount.objects.aggregate(s=Sum('due_amount'))['s'] or 0.0
    total_expenses = CollegeExpense.objects.aggregate(s=Sum('amount'))['s'] or 0.0
    total_scholarships = StudentFeeAccount.objects.aggregate(s=Sum('scholarship_amount'))['s'] or 0.0

    recent_payments = FeePayment.objects.order_by('-created_at')[:8]
    recent_expenses = CollegeExpense.objects.order_by('-created_at')[:8]

    # Department Budgets Summary
    budgets = DepartmentBudget.objects.all()

    context = {
        'page_title': 'Finance Management Dashboard',
        'total_fee_collected': round(total_fee_collected, 2),
        'total_fee_due': round(total_fee_due, 2),
        'total_expenses': round(total_expenses, 2),
        'total_scholarships': round(total_scholarships, 2),
        'net_balance': round(total_fee_collected - total_expenses, 2),
        'recent_payments': recent_payments,
        'recent_expenses': recent_expenses,
        'budgets': budgets,
    }
    return render(request, 'finance_template/finance_home.html', context)


# ==============================================================================
# FEE STRUCTURES
# ==============================================================================

@role_required(['5', '4', '1'])
def manage_fee_structures(request):
    structures = FeeStructure.objects.all().order_by('-created_at')
    courses = Course.objects.all()
    sessions = Session.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        course_id = request.POST.get('course')
        session_id = request.POST.get('session')
        academic_year = request.POST.get('academic_year', '2024-2025')
        tuition = float(request.POST.get('tuition_fee') or 0.0)
        development = float(request.POST.get('development_fee') or 0.0)
        exam = float(request.POST.get('exam_fee') or 0.0)
        lab = float(request.POST.get('lab_fee') or 0.0)
        library = float(request.POST.get('library_fee') or 0.0)
        other = float(request.POST.get('other_fee') or 0.0)

        course = get_object_or_404(Course, id=course_id)
        session = Session.objects.filter(id=session_id).first() if session_id else None

        fee_struct = FeeStructure.objects.create(
            name=name,
            course=course,
            session=session,
            academic_year=academic_year,
            tuition_fee=tuition,
            development_fee=development,
            exam_fee=exam,
            lab_fee=lab,
            library_fee=library,
            other_fee=other,
        )

        SystemAuditLog.objects.create(
            user=request.user,
            action="CREATE",
            module="Finance",
            description=f"Created fee structure '{name}' for {course.name} ({academic_year}): ₹{fee_struct.total_fee}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        messages.success(request, f"Fee structure '{name}' created successfully!")
        return redirect(reverse('manage_fee_structures'))

    context = {
        'page_title': 'Fee Structure Management',
        'structures': structures,
        'courses': courses,
        'sessions': sessions,
    }
    return render(request, 'finance_template/manage_fee_structures.html', context)


# ==============================================================================
# STUDENT FEE ACCOUNTS & PAYMENTS
# ==============================================================================

@role_required(['5', '4', '1'])
def student_fee_accounts(request):
    accounts = StudentFeeAccount.objects.select_related('student', 'fee_structure', 'student__admin', 'student__course').all()
    courses = Course.objects.all()
    structures = FeeStructure.objects.all()

    course_filter = request.GET.get('course', '')
    status_filter = request.GET.get('status', '')

    if course_filter:
        accounts = accounts.filter(student__course_id=course_filter)
    if status_filter:
        accounts = accounts.filter(status=status_filter)

    # Sync students without fee accounts
    all_students = Student.objects.filter(status='Active')
    for s in all_students:
        if not hasattr(s, 'fee_account'):
            # Auto-assign matching fee structure if available
            fs = FeeStructure.objects.filter(course=s.course).first()
            acc = StudentFeeAccount.objects.create(student=s, fee_structure=fs)
            acc.recalculate()

    context = {
        'page_title': 'Student Fee Accounts',
        'accounts': accounts,
        'courses': courses,
        'structures': structures,
        'selected_course': course_filter,
        'selected_status': status_filter,
    }
    return render(request, 'finance_template/student_fee_accounts.html', context)


@role_required(['5', '4', '1'])
def student_fee_detail(request, account_id):
    account = get_object_or_404(StudentFeeAccount, id=account_id)
    payments = account.payments.all().order_by('-payment_date')
    structures = FeeStructure.objects.filter(course=account.student.course)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'assign_structure':
            structure_id = request.POST.get('fee_structure')
            account.fee_structure = get_object_or_404(FeeStructure, id=structure_id)
            account.scholarship_amount = float(request.POST.get('scholarship_amount') or 0.0)
            account.concession_amount = float(request.POST.get('concession_amount') or 0.0)
            account.recalculate()
            messages.success(request, "Fee structure and concessions updated.")
            return redirect(reverse('student_fee_detail', args=[account.id]))

        elif action == 'record_payment':
            amount = float(request.POST.get('amount') or 0.0)
            mode = request.POST.get('payment_mode', 'Online')
            txn_ref = request.POST.get('transaction_reference', '')
            remarks = request.POST.get('remarks', '')

            if amount <= 0:
                messages.error(request, "Payment amount must be greater than zero.")
            else:
                receipt_no = f"REC-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"
                payment = FeePayment.objects.create(
                    student_fee_account=account,
                    receipt_number=receipt_no,
                    amount_paid=amount,
                    payment_mode=mode,
                    transaction_reference=txn_ref,
                    recorded_by=request.user,
                    remarks=remarks
                )
                account.recalculate()

                SystemAuditLog.objects.create(
                    user=request.user,
                    action="PAYMENT",
                    module="Finance",
                    description=f"Recorded fee payment of ₹{amount} for {account.student} (Receipt #{receipt_no})",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                messages.success(request, f"Payment of ₹{amount} recorded! Receipt: {receipt_no}")
                return redirect(reverse('student_fee_detail', args=[account.id]))

    context = {
        'page_title': f'Fee Details - {account.student}',
        'account': account,
        'payments': payments,
        'structures': structures,
    }
    return render(request, 'finance_template/student_fee_detail.html', context)


@role_required(['5', '4', '1'])
def process_fee_refund(request, payment_id):
    payment = get_object_or_404(FeePayment, id=payment_id)
    if request.method == 'POST':
        reason = request.POST.get('refund_reason', 'Administrative refund')
        payment.is_refunded = True
        payment.refund_reason = reason
        payment.save()
        payment.student_fee_account.recalculate()

        SystemAuditLog.objects.create(
            user=request.user,
            action="REFUND",
            module="Finance",
            description=f"Refunded payment #{payment.receipt_number} of ₹{payment.amount_paid} for {payment.student_fee_account.student}. Reason: {reason}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        messages.warning(request, f"Payment #{payment.receipt_number} marked as refunded.")
        return redirect(reverse('student_fee_detail', args=[payment.student_fee_account.id]))

    return redirect(reverse('finance_home'))


def view_receipt(request, payment_id):
    """
    Download formal fee payment receipt as a valid PDF attachment.
    Authorized for the owning Student (Role 3), or Finance (Role 5), Admin (Role 1), Principal (Role 4).
    Prevents unauthorized receipt access (horizontal privilege escalation).
    """
    if not request.user.is_authenticated:
        return redirect(reverse('login_page'))

    payment = get_object_or_404(FeePayment, id=payment_id)
    account = payment.student_fee_account
    student = account.student

    user_type = str(getattr(request.user, 'user_type', ''))

    # Security check: Students may only download their own receipts
    if user_type == '3':
        if student.admin != request.user:
            return HttpResponseForbidden("<h3>403 Forbidden: You are not authorized to view or download this receipt.</h3>")
    elif user_type not in ['1', '4', '5'] and not request.user.is_superuser:
        return HttpResponseForbidden("<h3>403 Forbidden: Unauthorized access to financial receipts.</h3>")

    # Format receipt data
    student_name = f"{student.admin.first_name} {student.admin.last_name}".strip() or student.admin.email
    course_name = student.course.name if student.course else "General"
    acad_year = account.fee_structure.academic_year if account.fee_structure else "2024-2025"
    fee_struct_name = account.fee_structure.name if account.fee_structure else "Institutional Academic Fees"
    recorded_by_name = str(payment.recorded_by) if payment.recorded_by else "Finance Office"

    receipt_data = {
        'college_name': 'SHRI INDIRA GANDHI COLLEGE OF ENGINEERING',
        'college_sub': 'Approved by AICTE | Affiliated to Mumbai University | NAAC Accredited',
        'college_address': 'Sector 8, Ghansoli, Navi Mumbai, Maharashtra - 400701',
        'receipt_no': payment.receipt_number,
        'payment_date': payment.payment_date.strftime('%d-%b-%Y') if payment.payment_date else str(date.today()),
        'payment_mode': payment.payment_mode or 'Online',
        'txn_ref': payment.transaction_reference or 'N/A',
        'status': 'REFUNDED' if payment.is_refunded else 'CONFIRMED',
        'student_name': student_name,
        'student_id': student.admission_number or f"STU-{student.id:04d}",
        'roll_no': student.roll_number or f"ROLL-{student.id:04d}",
        'department': course_name,
        'academic_year': acad_year,
        'semester': str(student.current_semester or 1),
        'section': student.section or 'A',
        'fee_structure_name': fee_struct_name,
        'amount_paid': payment.amount_paid,
        'net_fee': account.net_fee,
        'total_paid': account.paid_amount,
        'due_amount': account.due_amount,
        'recorded_by': recorded_by_name,
    }

    pdf_bytes = SimplePDF(title=f"Receipt-{payment.receipt_number}").build_receipt(receipt_data)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Receipt_{payment.receipt_number}.pdf"'
    return response


# ==============================================================================
# PAYROLL MANAGEMENT
# ==============================================================================

@role_required(['5', '4', '1'])
def manage_payroll(request):
    employees = CustomUser.objects.filter(user_type__in=['2', '5', '6', '7']).order_by('first_name')
    current_year = date.today().year
    current_month = date.today().month

    month_filter = int(request.GET.get('month', current_month))
    year_filter = int(request.GET.get('year', current_year))

    payrolls = Payroll.objects.filter(month=month_filter, year=year_filter).select_related('employee')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_payslip':
            emp_id = request.POST.get('employee')
            basic = float(request.POST.get('basic_salary') or 0.0)
            hra = float(request.POST.get('hra') or 0.0)
            allowances = float(request.POST.get('allowances') or 0.0)
            deductions = float(request.POST.get('deductions') or 0.0)
            month = int(request.POST.get('month'))
            year = int(request.POST.get('year'))

            emp = get_object_or_404(CustomUser, id=emp_id)
            payroll, created = Payroll.objects.update_or_create(
                employee=emp, month=month, year=year,
                defaults={
                    'basic_salary': basic,
                    'hra': hra,
                    'allowances': allowances,
                    'deductions': deductions,
                }
            )
            payroll.save()
            messages.success(request, f"Payslip for {emp} ({month}/{year}) saved successfully!")
            return redirect(f"{reverse('manage_payroll')}?month={month}&year={year}")

        elif action == 'mark_paid':
            payroll_id = request.POST.get('payroll_id')
            payroll = get_object_or_404(Payroll, id=payroll_id)
            payroll.status = "Paid"
            payroll.payment_date = date.today()
            payroll.save()

            SystemAuditLog.objects.create(
                user=request.user,
                action="PAYROLL",
                module="Finance",
                description=f"Marked payroll #{payroll.payslip_reference} as Paid (₹{payroll.net_salary})",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Payslip for {payroll.employee} marked as Paid!")
            return redirect(f"{reverse('manage_payroll')}?month={payroll.month}&year={payroll.year}")

    context = {
        'page_title': 'Staff Payroll Management',
        'payrolls': payrolls,
        'employees': employees,
        'selected_month': month_filter,
        'selected_year': year_filter,
        'months': range(1, 13),
    }
    return render(request, 'finance_template/manage_payroll.html', context)


# ==============================================================================
# COLLEGE EXPENDITURE & BUDGETS
# ==============================================================================

@role_required(['5', '4', '1'])
def manage_expenses(request):
    expenses = CollegeExpense.objects.all().order_by('-expense_date')
    courses = Course.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category')
        dept_id = request.POST.get('department')
        amount = float(request.POST.get('amount') or 0.0)
        invoice_no = request.POST.get('invoice_number', '')
        vendor = request.POST.get('vendor_name', '')
        expense_date = request.POST.get('expense_date') or str(date.today())
        academic_year = request.POST.get('academic_year', '2024-2025')
        invoice_file = request.FILES.get('invoice_file')

        dept = Course.objects.filter(id=dept_id).first() if dept_id else None

        expense = CollegeExpense.objects.create(
            title=title,
            category=category,
            department=dept,
            amount=amount,
            invoice_number=invoice_no,
            vendor_name=vendor,
            expense_date=expense_date,
            academic_year=academic_year,
            invoice_file=invoice_file,
            created_by=request.user
        )

        # Update matching department budget if assigned
        if dept:
            budget = DepartmentBudget.objects.filter(course=dept, financial_year=academic_year).first()
            if budget:
                budget.update_spending()

        SystemAuditLog.objects.create(
            user=request.user,
            action="EXPENSE",
            module="Finance",
            description=f"Recorded expense: [{category}] {title} - ₹{amount} (Vendor: {vendor})",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        messages.success(request, f"Expense '{title}' recorded successfully!")
        return redirect(reverse('manage_expenses'))

    context = {
        'page_title': 'Institutional Expenditure Management',
        'expenses': expenses,
        'courses': courses,
    }
    return render(request, 'finance_template/manage_expenses.html', context)


@role_required(['5', '4', '1'])
def manage_budgets(request):
    budgets = DepartmentBudget.objects.select_related('course').all()
    courses = Course.objects.all()

    # Recalculate spending
    for b in budgets:
        b.update_spending()

    if request.method == 'POST':
        course_id = request.POST.get('course')
        fin_year = request.POST.get('financial_year', '2024-2025')
        amount = float(request.POST.get('allocated_budget') or 0.0)

        course = get_object_or_404(Course, id=course_id)
        budget, created = DepartmentBudget.objects.update_or_create(
            course=course, financial_year=fin_year,
            defaults={'allocated_budget': amount}
        )
        budget.update_spending()

        SystemAuditLog.objects.create(
            user=request.user,
            action="BUDGET",
            module="Finance",
            description=f"Allocated budget of ₹{amount} to {course.name} for {fin_year}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        messages.success(request, f"Budget for {course.name} updated!")
        return redirect(reverse('manage_budgets'))

    context = {
        'page_title': 'Departmental Budget Allocations',
        'budgets': budgets,
        'courses': courses,
    }
    return render(request, 'finance_template/manage_budgets.html', context)


@role_required(['5', '4', '1'])
def financial_reports(request):
    total_income = FeePayment.objects.filter(is_refunded=False).aggregate(s=Sum('amount_paid'))['s'] or 0.0
    total_expenses = CollegeExpense.objects.aggregate(s=Sum('amount'))['s'] or 0.0
    total_outstanding = StudentFeeAccount.objects.aggregate(s=Sum('due_amount'))['s'] or 0.0

    # Expense by Category
    categories = CollegeExpense.objects.values('category').annotate(total=Sum('amount')).order_by('-total')

    # Fee by Department
    dept_fees = StudentFeeAccount.objects.values('student__course__name').annotate(
        collected=Sum('paid_amount'),
        due=Sum('due_amount')
    ).order_by('-collected')

    context = {
        'page_title': 'Consolidated Financial Reports',
        'total_income': round(total_income, 2),
        'total_expenses': round(total_expenses, 2),
        'total_outstanding': round(total_outstanding, 2),
        'net_surplus': round(total_income - total_expenses, 2),
        'categories': categories,
        'dept_fees': dept_fees,
    }
    return render(request, 'finance_template/financial_reports.html', context)
