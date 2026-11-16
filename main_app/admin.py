from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Admin, Principal, FinanceOfficer, HROfficer, AccreditationCoordinator,
    Course, Book, IssuedBook, Library, Student, Staff, Subject, Session,
    Attendance, AttendanceReport, AttendanceCorrectionLog,
    LeaveReportStudent, LeaveReportStaff, FeedbackStudent, FeedbackStaff,
    NotificationStudent, NotificationStaff, StudentResult, MarksCorrectionLog,
    StudentAchievement, StudentPlacement,
    FacultyQualification, FacultyPublication, FacultyTraining, FacultyPatent,
    FeeStructure, StudentFeeAccount, FeePayment, Payroll, CollegeExpense, DepartmentBudget,
    EmployeeRecord, LeaveQuota, RecruitmentRecord,
    NAACCriterion, NAACMetricData,
    NBAProgram, ProgramEducationalObjective, ProgramOutcome, ProgramSpecificOutcome,
    CourseOutcome, COPOMapping, COAttainmentRecord, ContinuousImprovementAction,
    InstitutionalDocument, SystemAuditLog
)


class UserModel(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')


admin.site.register(CustomUser, UserModel)
admin.site.register(Admin)
admin.site.register(Principal)
admin.site.register(FinanceOfficer)
admin.site.register(HROfficer)
admin.site.register(AccreditationCoordinator)

admin.site.register(Course)
admin.site.register(Book)
admin.site.register(IssuedBook)
admin.site.register(Library)
admin.site.register(Student)
admin.site.register(Staff)
admin.site.register(Subject)
admin.site.register(Session)

admin.site.register(Attendance)
admin.site.register(AttendanceReport)
admin.site.register(AttendanceCorrectionLog)
admin.site.register(LeaveReportStudent)
admin.site.register(LeaveReportStaff)
admin.site.register(FeedbackStudent)
admin.site.register(FeedbackStaff)
admin.site.register(NotificationStudent)
admin.site.register(NotificationStaff)
admin.site.register(StudentResult)
admin.site.register(MarksCorrectionLog)

admin.site.register(StudentAchievement)
admin.site.register(StudentPlacement)
admin.site.register(FacultyQualification)
admin.site.register(FacultyPublication)
admin.site.register(FacultyTraining)
admin.site.register(FacultyPatent)

admin.site.register(FeeStructure)
admin.site.register(StudentFeeAccount)
admin.site.register(FeePayment)
admin.site.register(Payroll)
admin.site.register(CollegeExpense)
admin.site.register(DepartmentBudget)

admin.site.register(EmployeeRecord)
admin.site.register(LeaveQuota)
admin.site.register(RecruitmentRecord)

admin.site.register(NAACCriterion)
admin.site.register(NAACMetricData)

admin.site.register(NBAProgram)
admin.site.register(ProgramEducationalObjective)
admin.site.register(ProgramOutcome)
admin.site.register(ProgramSpecificOutcome)
admin.site.register(CourseOutcome)
admin.site.register(COPOMapping)
admin.site.register(COAttainmentRecord)
admin.site.register(ContinuousImprovementAction)

admin.site.register(InstitutionalDocument)
admin.site.register(SystemAuditLog)
