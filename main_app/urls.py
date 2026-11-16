from django.urls import path

from main_app.EditResultView import EditResultView
from . import (
    hod_views, staff_views, student_views, views,
    principal_views, finance_views, hr_views, accreditation_views
)

urlpatterns = [
    # Core Authentication & Utilities
    path("", views.login_page, name='login_page'),
    path("get_attendance", views.get_attendance, name='get_attendance'),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name='showFirebaseJS'),
    path("doLogin/", views.doLogin, name='user_login'),
    path("logout_user/", views.logout_user, name='user_logout'),

    # Principal Portal (Role 4)
    path("principal/home/", principal_views.principal_home, name='principal_home'),
    path("principal/students/", principal_views.principal_view_students, name='principal_students'),
    path("principal/faculty/", principal_views.principal_view_faculty, name='principal_faculty'),
    path("principal/finance/", principal_views.principal_view_finance, name='principal_finance'),
    path("principal/accreditation/", principal_views.principal_view_accreditation, name='principal_accreditation'),

    # Admin / HOD Portal (Role 1)
    path("admin/home/", hod_views.admin_home, name='admin_home'),
    path("staff/add", hod_views.add_staff, name='add_staff'),
    path("course/add", hod_views.add_course, name='add_course'),
    path("send_student_notification/", hod_views.send_student_notification, name='send_student_notification'),
    path("send_staff_notification/", hod_views.send_staff_notification, name='send_staff_notification'),
    path("add_session/", hod_views.add_session, name='add_session'),
    path("admin_notify_student", hod_views.admin_notify_student, name='admin_notify_student'),
    path("admin_notify_staff", hod_views.admin_notify_staff, name='admin_notify_staff'),
    path("admin_view_profile", hod_views.admin_view_profile, name='admin_view_profile'),
    path("check_email_availability", hod_views.check_email_availability, name="check_email_availability"),
    path("session/manage/", hod_views.manage_session, name='manage_session'),
    path("session/edit/<int:session_id>", hod_views.edit_session, name='edit_session'),
    path("student/view/feedback/", hod_views.student_feedback_message, name="student_feedback_message"),
    path("staff/view/feedback/", hod_views.staff_feedback_message, name="staff_feedback_message"),
    path("student/view/leave/", hod_views.view_student_leave, name="view_student_leave"),
    path("staff/view/leave/", hod_views.view_staff_leave, name="view_staff_leave"),
    path("attendance/view/", hod_views.admin_view_attendance, name="admin_view_attendance"),
    path("attendance/fetch/", hod_views.get_admin_attendance, name='get_admin_attendance'),
    path("student/add/", hod_views.add_student, name='add_student'),
    path("subject/add/", hod_views.add_subject, name='add_subject'),
    path("staff/manage/", hod_views.manage_staff, name='manage_staff'),
    path("student/manage/", hod_views.manage_student, name='manage_student'),
    path("course/manage/", hod_views.manage_course, name='manage_course'),
    path("subject/manage/", hod_views.manage_subject, name='manage_subject'),
    path("staff/edit/<int:staff_id>", hod_views.edit_staff, name='edit_staff'),
    path("staff/delete/<int:staff_id>", hod_views.delete_staff, name='delete_staff'),
    path("staff/status/<int:staff_id>/", hod_views.toggle_staff_status, name='toggle_staff_status'),
    path("course/delete/<int:course_id>", hod_views.delete_course, name='delete_course'),
    path("subject/delete/<int:subject_id>", hod_views.delete_subject, name='delete_subject'),
    path("session/delete/<int:session_id>", hod_views.delete_session, name='delete_session'),
    path("student/delete/<int:student_id>", hod_views.delete_student, name='delete_student'),
    path("student/status/<int:student_id>/", hod_views.toggle_student_status, name='toggle_student_status'),
    path("student/edit/<int:student_id>", hod_views.edit_student, name='edit_student'),
    path("course/edit/<int:course_id>", hod_views.edit_course, name='edit_course'),
    path("subject/edit/<int:subject_id>", hod_views.edit_subject, name='edit_subject'),

    # Institutional Repository & Audits
    path("institutional/documents/", hod_views.institutional_documents, name='institutional_documents'),
    path("institutional/documents/verify/<int:doc_id>/", hod_views.verify_institutional_document, name='verify_institutional_document'),
    path("system/audit-logs/", hod_views.system_audit_logs, name='system_audit_logs'),
    path("institutional/reports/", hod_views.centralized_reports, name='centralized_reports'),

    # Alumni Management
    path("alumni/list/", hod_views.alumni_list, name='alumni_list'),
    path("alumni/<int:alumni_id>/", hod_views.alumni_detail, name='alumni_detail'),
    path("student/graduate/<int:student_id>/", hod_views.graduate_student, name='graduate_student'),

    # Staff / Faculty Portal (Role 2)
    path("staff/home/", staff_views.staff_home, name='staff_home'),
    path("staff/portfolio/", staff_views.staff_portfolio, name='staff_portfolio'),
    path("staff/apply/leave/", staff_views.staff_apply_leave, name='staff_apply_leave'),
    path("staff/feedback/", staff_views.staff_feedback, name='staff_feedback'),
    path("staff/view/profile/", staff_views.staff_view_profile, name='staff_view_profile'),
    path("staff/attendance/take/", staff_views.staff_take_attendance, name='staff_take_attendance'),
    path("staff/attendance/update/", staff_views.staff_update_attendance, name='staff_update_attendance'),
    path("staff/get_students/", staff_views.get_students, name='get_students'),
    path("staff/attendance/fetch/", staff_views.get_student_attendance, name='get_student_attendance'),
    path("staff/attendance/save/", staff_views.save_attendance, name='save_attendance'),
    path("staff/attendance/update_save/", staff_views.update_attendance, name='update_attendance'),
    path("staff/fcmtoken/", staff_views.staff_fcmtoken, name='staff_fcmtoken'),
    path("staff/view/notification/", staff_views.staff_view_notification, name="staff_view_notification"),
    path("staff/result/add/", staff_views.staff_add_result, name='staff_add_result'),
    path("staff/result/edit/", EditResultView.as_view(), name='edit_student_result'),
    path("staff/result/fetch/", staff_views.fetch_student_result, name='fetch_student_result'),
    path("staff/result/finalize/<int:subject_id>/", staff_views.finalize_subject_results, name='finalize_subject_results'),
    path("staff/addbook/", staff_views.add_book, name="add_book"),
    path("staff/issue_book/", staff_views.issue_book, name="issue_book"),
    path("staff/view_issued_book/", staff_views.view_issued_book, name="view_issued_book"),

    # Student Portal (Role 3)
    path("student/home/", student_views.student_home, name='student_home'),
    path("student/fees/", student_views.student_view_fees, name='student_view_fees'),
    path("student/portfolio/", student_views.student_portfolio, name='student_portfolio'),
    path("student/view/attendance/", student_views.student_view_attendance, name='student_view_attendance'),
    path("student/apply/leave/", student_views.student_apply_leave, name='student_apply_leave'),
    path("student/feedback/", student_views.student_feedback, name='student_feedback'),
    path("student/view/profile/", student_views.student_view_profile, name='student_view_profile'),
    path("student/fcmtoken/", student_views.student_fcmtoken, name='student_fcmtoken'),
    path("student/viewbooks/", student_views.view_books, name="view_books"),
    path("student/view/notification/", student_views.student_view_notification, name="student_view_notification"),
    path("student/view/result/", student_views.student_view_result, name='student_view_result'),

    # Finance Portal (Role 5)
    path("finance/home/", finance_views.finance_home, name='finance_home'),
    path("finance/fee-structures/", finance_views.manage_fee_structures, name='manage_fee_structures'),
    path("finance/student-accounts/", finance_views.student_fee_accounts, name='student_fee_accounts'),
    path("finance/student-account/<int:account_id>/", finance_views.student_fee_detail, name='student_fee_detail'),
    path("finance/refund/<int:payment_id>/", finance_views.process_fee_refund, name='process_fee_refund'),
    path("finance/receipt/<int:payment_id>/", finance_views.view_receipt, name='view_receipt'),
    path("finance/payroll/", finance_views.manage_payroll, name='manage_payroll'),
    path("finance/expenses/", finance_views.manage_expenses, name='manage_expenses'),
    path("finance/budgets/", finance_views.manage_budgets, name='manage_budgets'),
    path("finance/reports/", finance_views.financial_reports, name='financial_reports'),

    # HR Portal (Role 6)
    path("hr/home/", hr_views.hr_home, name='hr_home'),
    path("hr/employees/", hr_views.employee_list, name='employee_list'),
    path("hr/employee/<int:staff_id>/", hr_views.employee_detail, name='employee_detail'),
    path("hr/leaves/", hr_views.hr_leave_management, name='hr_leave_management'),
    path("hr/recruitments/", hr_views.recruitment_list, name='recruitment_list'),

    # Accreditation Portal (Role 7: NAAC & NBA)
    path("accreditation/home/", accreditation_views.accreditation_home, name='accreditation_home'),
    path("accreditation/naac/criterion/<int:criterion_id>/", accreditation_views.naac_criterion_detail, name='naac_criterion_detail'),
    path("accreditation/naac/report/", accreditation_views.naac_report, name='naac_report'),
    path("accreditation/nba/programs/", accreditation_views.nba_programs_list, name='nba_programs_list'),
    path("accreditation/nba/program/<int:program_id>/", accreditation_views.nba_program_detail, name='nba_program_detail'),
    path("accreditation/nba/mapping/<int:subject_id>/", accreditation_views.subject_co_po_mapping, name='subject_co_po_mapping'),
]
