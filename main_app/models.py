from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager, AbstractUser
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from datetime import datetime, timedelta, date


class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = CustomUser(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        assert extra_fields["is_staff"]
        assert extra_fields["is_superuser"]
        return self._create_user(email, password, **extra_fields)


class Session(models.Model):
    start_year = models.DateField()
    end_year = models.DateField()

    def __str__(self):
        return "From " + str(self.start_year) + " to " + str(self.end_year)


class CustomUser(AbstractUser):
    USER_TYPE = (
        (1, "Admin"),
        (2, "Staff"),
        (3, "Student"),
        (4, "Principal"),
        (5, "Finance"),
        (6, "HR"),
        (7, "Accreditation"),
    )
    GENDER = [("M", "Male"), ("F", "Female"), ("O", "Other")]

    username = None  # Removed username, using email instead
    email = models.EmailField(unique=True)
    user_type = models.CharField(default=1, choices=USER_TYPE, max_length=2)
    gender = models.CharField(max_length=1, choices=GENDER, default="M")
    profile_pic = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    address = models.TextField(blank=True, default="")
    fcm_token = models.TextField(default="")  # For firebase notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    @property
    def role_name(self):
        roles = dict(self.USER_TYPE)
        try:
            return roles.get(int(self.user_type), "User")
        except (ValueError, TypeError):
            return "User"


class Admin(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.admin)


class Principal(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"Principal: {self.admin}"


class FinanceOfficer(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"Finance: {self.admin}"


class HROfficer(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"HR: {self.admin}"


class AccreditationCoordinator(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"Accreditation: {self.admin}"


class Course(models.Model):
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    name = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.PositiveIntegerField()
    category = models.CharField(max_length=50)

    def __str__(self):
        return str(self.name) + " [" + str(self.isbn) + "]"


class Student(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Graduated", "Graduated"),
        ("Alumni", "Alumni"),
        ("Inactive", "Inactive"),
    ]

    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING, null=True)
    admission_number = models.CharField(max_length=50, blank=True, null=True, unique=False)
    roll_number = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    parent_name = models.CharField(max_length=150, blank=True, null=True)
    parent_phone = models.CharField(max_length=20, blank=True, null=True)
    current_semester = models.IntegerField(default=1)
    section = models.CharField(max_length=10, blank=True, null=True, default="A")
    status = models.CharField(max_length=20, default="Active", choices=STATUS_CHOICES)
    sgpa = models.FloatField(default=0.0)
    cgpa = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.admin.last_name}, {self.admin.first_name}"


class AlumniProfile(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="alumni_profile")
    graduation_year = models.IntegerField(default=2024)
    degree_awarded = models.CharField(max_length=150, default="Bachelor of Technology")
    current_company = models.CharField(max_length=200, blank=True, null=True)
    current_designation = models.CharField(max_length=150, blank=True, null=True)
    current_city = models.CharField(max_length=100, blank=True, null=True)
    higher_education_institution = models.CharField(max_length=250, blank=True, null=True)
    higher_education_degree = models.CharField(max_length=150, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    engagement_notes = models.TextField(blank=True, null=True)
    is_notable = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Alumni: {self.student} (Class of {self.graduation_year})"


class Library(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=False)

    def __str__(self):
        return str(self.student)


def expiry():
    return datetime.today() + timedelta(days=14)


class IssuedBook(models.Model):
    student_id = models.CharField(max_length=100, blank=True)
    isbn = models.CharField(max_length=13)
    issued_date = models.DateField(auto_now=True)
    expiry_date = models.DateField(default=expiry)


class Staff(models.Model):
    EMPLOYMENT_STATUS = [
        ("Active", "Active"),
        ("On Leave", "On Leave"),
        ("Resigned", "Resigned"),
        ("Retired", "Retired"),
    ]

    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    faculty_id = models.CharField(max_length=50, blank=True, null=True)
    designation = models.CharField(max_length=100, default="Assistant Professor")
    department = models.CharField(max_length=100, blank=True, null=True)
    date_of_joining = models.DateField(blank=True, null=True)
    employment_status = models.CharField(max_length=20, default="Active", choices=EMPLOYMENT_STATUS)
    total_experience_years = models.FloatField(default=0.0)
    highest_qualification = models.CharField(max_length=100, blank=True, null=True)
    specialization = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.admin.first_name + " " + self.admin.last_name


class Subject(models.Model):
    name = models.CharField(max_length=120)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Attendance(models.Model):
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING)
    subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject.name} - {self.date}"


class AttendanceReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    attendance_status = models.CharField(
        max_length=20,
        default="Present",
        choices=[("Present", "Present"), ("Absent", "Absent"), ("Excused", "Excused"), ("On Duty", "On Duty")]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.attendance.date}: {'Present' if self.status else 'Absent'}"


class AttendanceCorrectionLog(models.Model):
    attendance_report = models.ForeignKey(AttendanceReport, on_delete=models.CASCADE)
    changed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    previous_status = models.BooleanField()
    new_status = models.BooleanField()
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attendance Correction #{self.id} by {self.changed_by}"


class LeaveReportStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)  # 0: Pending, 1: Approved, 2: Rejected
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)  # 0: Pending, 1: Approved, 2: Rejected
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StudentResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    test = models.FloatField(default=0)
    exam = models.FloatField(default=0)
    assignment = models.FloatField(default=0)
    practical = models.FloatField(default=0)
    project = models.FloatField(default=0)
    total = models.FloatField(default=0)
    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(blank=True, null=True)
    finalized_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="finalized_results"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.total = float(self.test) + float(self.exam) + float(self.assignment) + float(self.practical) + float(self.project)
        super(StudentResult, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.subject}: {self.total}"


class MarksCorrectionLog(models.Model):
    result = models.ForeignKey(StudentResult, on_delete=models.CASCADE)
    changed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    previous_test = models.FloatField(default=0)
    new_test = models.FloatField(default=0)
    previous_exam = models.FloatField(default=0)
    new_exam = models.FloatField(default=0)
    previous_assignment = models.FloatField(default=0)
    new_assignment = models.FloatField(default=0)
    previous_practical = models.FloatField(default=0)
    new_practical = models.FloatField(default=0)
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Marks Correction #{self.id} for {self.result.student} by {self.changed_by}"


# ==============================================================================
# STUDENT ACHIEVEMENTS, INTERNSHIPS, PLACEMENTS
# ==============================================================================

class StudentAchievement(models.Model):
    CATEGORY_CHOICES = [
        ("Paper", "Research Paper"),
        ("Patent", "Patent"),
        ("Hackathon", "Hackathon"),
        ("Certification", "Certification"),
        ("Internship", "Internship"),
        ("Competition", "Technical Competition"),
        ("Extracurricular", "Extracurricular Achievement"),
        ("Project", "Capstone / Research Project"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="achievements")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=250)
    event_name = models.CharField(max_length=200, blank=True, null=True)
    organization = models.CharField(max_length=200, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    academic_year = models.CharField(max_length=20, default="2024-2025")
    description = models.TextField(blank=True, null=True)
    certificate = models.FileField(upload_to="student_achievements/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - [{self.category}] {self.title}"


class StudentPlacement(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="placements")
    company_name = models.CharField(max_length=200)
    designation = models.CharField(max_length=150, default="Software Engineer")
    package_lpa = models.FloatField(default=0.0)
    offer_date = models.DateField(blank=True, null=True)
    academic_year = models.CharField(max_length=20, default="2024-2025")
    offer_letter = models.FileField(upload_to="placements/", blank=True, null=True)
    is_higher_studies = models.BooleanField(default=False)
    institution_name = models.CharField(max_length=250, blank=True, null=True)
    qualifying_exam = models.CharField(max_length=100, blank=True, null=True)  # GATE, GRE, CAT, etc.
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} placed at {self.company_name} ({self.package_lpa} LPA)"


# ==============================================================================
# FACULTY PORTFOLIO: QUALIFICATIONS, PUBLICATIONS, TRAININGS, PATENTS
# ==============================================================================

class FacultyQualification(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="qualifications")
    degree = models.CharField(max_length=150)  # Ph.D, M.Tech, M.E, B.Tech
    specialization = models.CharField(max_length=150)
    institution = models.CharField(max_length=250)
    year_of_completion = models.IntegerField()
    certificate = models.FileField(upload_to="faculty_qualifications/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff} - {self.degree} in {self.specialization}"


class FacultyPublication(models.Model):
    TYPE_CHOICES = [
        ("Journal", "Journal Paper"),
        ("Conference", "Conference Paper"),
        ("Book Chapter", "Book / Book Chapter"),
        ("Patent", "Patent"),
    ]
    INDEXING_CHOICES = [
        ("Scopus", "Scopus"),
        ("Web of Science", "Web of Science"),
        ("UGC Care", "UGC Care"),
        ("Peer Reviewed", "Peer Reviewed"),
        ("Other", "Other"),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="publications")
    publication_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default="Journal")
    title = models.CharField(max_length=300)
    journal_or_conference_name = models.CharField(max_length=300)
    issn_isbn = models.CharField(max_length=50, blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    academic_year = models.CharField(max_length=20, default="2024-2025")
    indexing = models.CharField(max_length=30, choices=INDEXING_CHOICES, default="Scopus")
    doi = models.CharField(max_length=150, blank=True, null=True)
    document = models.FileField(upload_to="faculty_publications/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff} - {self.title}"


class FacultyTraining(models.Model):
    TYPE_CHOICES = [
        ("FDP", "Faculty Development Programme"),
        ("Workshop", "Workshop"),
        ("Seminar", "Seminar"),
        ("STTP", "Short Term Training Program"),
        ("Conference", "Conference / Symposium"),
    ]
    ROLE_CHOICES = [
        ("Attended", "Attended"),
        ("Conducted", "Conducted / Organised"),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="trainings")
    training_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="Attended")
    title = models.CharField(max_length=300)
    organizing_body = models.CharField(max_length=250)
    duration_days = models.IntegerField(default=1)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    academic_year = models.CharField(max_length=20, default="2024-2025")
    certificate = models.FileField(upload_to="faculty_trainings/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff} - [{self.role}] {self.title}"


class FacultyPatent(models.Model):
    STATUS_CHOICES = [
        ("Filed", "Filed"),
        ("Published", "Published"),
        ("Granted", "Granted"),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="patents")
    title = models.CharField(max_length=300)
    application_number = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Filed")
    filing_date = models.DateField(blank=True, null=True)
    grant_date = models.DateField(blank=True, null=True)
    patent_office = models.CharField(max_length=150, default="Indian Patent Office")
    document = models.FileField(upload_to="faculty_patents/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff} - {self.title} ({self.status})"


# ==============================================================================
# FINANCE MODULE: FEES, PAYMENTS, PAYROLL, EXPENSES, BUDGETS
# ==============================================================================

class FeeStructure(models.Model):
    name = models.CharField(max_length=150)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True)
    academic_year = models.CharField(max_length=20, default="2024-2025")
    tuition_fee = models.FloatField(default=0.0)
    development_fee = models.FloatField(default=0.0)
    exam_fee = models.FloatField(default=0.0)
    lab_fee = models.FloatField(default=0.0)
    library_fee = models.FloatField(default=0.0)
    other_fee = models.FloatField(default=0.0)
    total_fee = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_fee = (
            float(self.tuition_fee)
            + float(self.development_fee)
            + float(self.exam_fee)
            + float(self.lab_fee)
            + float(self.library_fee)
            + float(self.other_fee)
        )
        super(FeeStructure, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.course} ({self.academic_year}): ₹{self.total_fee}"


class StudentFeeAccount(models.Model):
    STATUS_CHOICES = [
        ("Paid", "Paid"),
        ("Partially Paid", "Partially Paid"),
        ("Pending", "Pending"),
        ("Overdue", "Overdue"),
    ]

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="fee_account")
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.SET_NULL, null=True)
    scholarship_amount = models.FloatField(default=0.0)
    concession_amount = models.FloatField(default=0.0)
    net_fee = models.FloatField(default=0.0)
    paid_amount = models.FloatField(default=0.0)
    due_amount = models.FloatField(default=0.0)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    updated_at = models.DateTimeField(auto_now=True)

    def recalculate(self):
        base_fee = self.fee_structure.total_fee if self.fee_structure else 0.0
        self.net_fee = max(0.0, base_fee - float(self.scholarship_amount) - float(self.concession_amount))
        payments_sum = sum(p.amount_paid for p in self.payments.filter(is_refunded=False))
        self.paid_amount = payments_sum
        self.due_amount = max(0.0, self.net_fee - self.paid_amount)
        if self.paid_amount >= self.net_fee and self.net_fee > 0:
            self.status = "Paid"
        elif self.paid_amount > 0:
            self.status = "Partially Paid"
        else:
            self.status = "Pending"
        self.save()

    def __str__(self):
        return f"Fee Account: {self.student} [Due: ₹{self.due_amount}]"


class FeePayment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ("Cash", "Cash"),
        ("Cheque", "Cheque"),
        ("Online", "Online / UPI"),
        ("DD", "Demand Draft"),
        ("Bank Transfer", "Bank Transfer"),
    ]

    student_fee_account = models.ForeignKey(StudentFeeAccount, on_delete=models.CASCADE, related_name="payments")
    receipt_number = models.CharField(max_length=60, unique=True)
    amount_paid = models.FloatField()
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default="Online")
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateField(default=date.today)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    remarks = models.TextField(blank=True, null=True)
    is_refunded = models.BooleanField(default=False)
    refund_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt #{self.receipt_number} - ₹{self.amount_paid}"


class Payroll(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
    ]

    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="payrolls")
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    basic_salary = models.FloatField(default=0.0)
    hra = models.FloatField(default=0.0)
    allowances = models.FloatField(default=0.0)
    deductions = models.FloatField(default=0.0)
    net_salary = models.FloatField(default=0.0)
    payment_date = models.DateField(blank=True, null=True)
    payment_mode = models.CharField(max_length=50, default="Bank Transfer")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    payslip_reference = models.CharField(max_length=60, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.net_salary = float(self.basic_salary) + float(self.hra) + float(self.allowances) - float(self.deductions)
        if not self.payslip_reference:
            self.payslip_reference = f"PAY-{self.year}-{self.month:02d}-{self.employee.id}"
        super(Payroll, self).save(*args, **kwargs)

    def __str__(self):
        return f"Payslip: {self.employee} ({self.month}/{self.year}) - ₹{self.net_salary}"


class CollegeExpense(models.Model):
    CATEGORY_CHOICES = [
        ("Infrastructure", "Infrastructure"),
        ("Lab Equipment", "Laboratory & Equipment"),
        ("Maintenance", "Maintenance & Repairs"),
        ("Utilities", "Utilities (Electricity, Water, Internet)"),
        ("Department Expense", "Departmental Operations"),
        ("R&D", "Research & Development"),
        ("FDP & Training", "Faculty Development & Training"),
        ("Library Resources", "Books & Library Resources"),
        ("Other", "Other Institutional Expenditure"),
    ]

    title = models.CharField(max_length=250)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)
    department = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.FloatField()
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    vendor_name = models.CharField(max_length=200, blank=True, null=True)
    expense_date = models.DateField(default=date.today)
    academic_year = models.CharField(max_length=20, default="2024-2025")
    invoice_file = models.FileField(upload_to="expenses/", blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.category}] {self.title} - ₹{self.amount}"


class DepartmentBudget(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="budgets")
    financial_year = models.CharField(max_length=20, default="2024-2025")
    allocated_budget = models.FloatField(default=0.0)
    spent_amount = models.FloatField(default=0.0)
    remaining_budget = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def update_spending(self):
        expenses = CollegeExpense.objects.filter(department=self.course, academic_year=self.financial_year)
        self.spent_amount = sum(e.amount for e in expenses)
        self.remaining_budget = max(0.0, self.allocated_budget - self.spent_amount)
        self.save()

    def __str__(self):
        return f"{self.course} Budget ({self.financial_year}): ₹{self.allocated_budget}"


# ==============================================================================
# HR MODULE: EMPLOYEE MASTER, LEAVE QUOTA, RECRUITMENT
# ==============================================================================

class EmployeeRecord(models.Model):
    EMPLOYMENT_TYPES = [
        ("Permanent", "Permanent / Regular"),
        ("Contract", "Contractual"),
        ("Visiting", "Visiting / Adjunct"),
        ("Ad-hoc", "Ad-hoc"),
    ]
    SERVICE_STATUS = [
        ("In Service", "In Service"),
        ("Resigned", "Resigned"),
        ("Retired", "Retired"),
        ("Terminated", "Terminated"),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="employee_record")
    employee_id = models.CharField(max_length=50, unique=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_joining = models.DateField(blank=True, null=True)
    date_of_leaving = models.DateField(blank=True, null=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default="Permanent")
    service_status = models.CharField(max_length=20, choices=SERVICE_STATUS, default="In Service")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Employee #{self.employee_id} - {self.user}"


class LeaveQuota(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="leave_quotas")
    academic_year = models.CharField(max_length=20, default="2024-2025")
    casual_leave_total = models.IntegerField(default=12)
    casual_leave_taken = models.IntegerField(default=0)
    medical_leave_total = models.IntegerField(default=10)
    medical_leave_taken = models.IntegerField(default=0)
    duty_leave_total = models.IntegerField(default=15)
    duty_leave_taken = models.IntegerField(default=0)

    @property
    def casual_leave_remaining(self):
        return max(0, self.casual_leave_total - self.casual_leave_taken)

    @property
    def medical_leave_remaining(self):
        return max(0, self.medical_leave_total - self.medical_leave_taken)

    @property
    def duty_leave_remaining(self):
        return max(0, self.duty_leave_total - self.duty_leave_taken)

    def __str__(self):
        return f"Leave Quota: {self.user} ({self.academic_year})"


class RecruitmentRecord(models.Model):
    STATUS_CHOICES = [
        ("Applied", "Applied"),
        ("Shortlisted", "Shortlisted"),
        ("Interviewed", "Interviewed"),
        ("Selected", "Selected"),
        ("Rejected", "Rejected"),
    ]

    department = models.ForeignKey(Course, on_delete=models.CASCADE)
    position = models.CharField(max_length=150)
    applicant_name = models.CharField(max_length=200)
    applicant_email = models.EmailField()
    applicant_phone = models.CharField(max_length=20)
    application_date = models.DateField(default=date.today)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Applied")
    resume = models.FileField(upload_to="recruitment/", blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant_name} - {self.position} [{self.status}]"


# ==============================================================================
# NAAC ACCREDITATION MANAGEMENT (7 CRITERIA)
# ==============================================================================

class NAACCriterion(models.Model):
    criterion_number = models.IntegerField(unique=True)  # 1 to 7
    name = models.CharField(max_length=200)
    weightage = models.IntegerField(default=100)
    description = models.TextField()

    def __str__(self):
        return f"Criterion {self.criterion_number}: {self.name}"


class NAACMetricData(models.Model):
    criterion = models.ForeignKey(NAACCriterion, on_delete=models.CASCADE, related_name="metrics")
    metric_code = models.CharField(max_length=20)  # e.g. "1.1.1", "3.2.1"
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, null=True)
    academic_year = models.CharField(max_length=20, default="2024-2025")
    department = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    quantitative_value = models.FloatField(default=0.0)
    qualitative_notes = models.TextField(blank=True, null=True)
    supporting_document = models.FileField(upload_to="naac_evidence/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.metric_code}] {self.title} ({self.academic_year})"


# ==============================================================================
# NBA ACCREDITATION MANAGEMENT (OUTCOME-BASED EDUCATION)
# ==============================================================================

class NBAProgram(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name="nba_program")
    program_name = models.CharField(max_length=200)
    coordinator = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    tier = models.CharField(max_length=20, default="Tier II", choices=[("Tier I", "Tier I"), ("Tier II", "Tier II")])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"NBA Program: {self.program_name} ({self.course.name})"


class ProgramEducationalObjective(models.Model):
    program = models.ForeignKey(NBAProgram, on_delete=models.CASCADE, related_name="peos")
    code = models.CharField(max_length=10)  # PEO1, PEO2...
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return f"{self.program.program_name} - {self.code}"


class ProgramOutcome(models.Model):
    program = models.ForeignKey(NBAProgram, on_delete=models.CASCADE, related_name="pos")
    code = models.CharField(max_length=10)  # PO1 to PO12
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return f"{self.program.program_name} - {self.code}"


class ProgramSpecificOutcome(models.Model):
    program = models.ForeignKey(NBAProgram, on_delete=models.CASCADE, related_name="psos")
    code = models.CharField(max_length=10)  # PSO1, PSO2...
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return f"{self.program.program_name} - {self.code}"


class CourseOutcome(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="course_outcomes")
    code = models.CharField(max_length=10)  # CO1, CO2...
    description = models.TextField()
    target_percentage = models.FloatField(default=60.0)  # e.g., 60% marks
    attainment_target_students_percentage = models.FloatField(default=70.0)  # e.g., 70% of students should meet target

    def __str__(self):
        return f"{self.subject.name} - {self.code}"


class COPOMapping(models.Model):
    CORRELATION_LEVELS = [
        (0, "0 - No correlation"),
        (1, "1 - Low"),
        (2, "2 - Medium"),
        (3, "3 - High"),
    ]

    course_outcome = models.ForeignKey(CourseOutcome, on_delete=models.CASCADE, related_name="mappings")
    po = models.ForeignKey(ProgramOutcome, on_delete=models.CASCADE, null=True, blank=True)
    pso = models.ForeignKey(ProgramSpecificOutcome, on_delete=models.CASCADE, null=True, blank=True)
    correlation_level = models.IntegerField(default=0, choices=CORRELATION_LEVELS)
    justification = models.TextField(blank=True, null=True)

    def __str__(self):
        target = self.po.code if self.po else (self.pso.code if self.pso else "None")
        return f"{self.course_outcome.subject.name} {self.course_outcome.code} -> {target} ({self.correlation_level})"


class COAttainmentRecord(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    course_outcome = models.ForeignKey(CourseOutcome, on_delete=models.CASCADE)
    direct_attainment = models.FloatField(default=0.0)  # Scale 0 to 3
    indirect_attainment = models.FloatField(default=0.0)  # Scale 0 to 3
    overall_attainment = models.FloatField(default=0.0)  # Scale 0 to 3
    target_achieved = models.BooleanField(default=False)
    calculated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course_outcome} Attainment: {self.overall_attainment:.2f}/3.0"


class ContinuousImprovementAction(models.Model):
    STATUS_CHOICES = [
        ("Proposed", "Proposed"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
    ]

    program = models.ForeignKey(NBAProgram, on_delete=models.CASCADE, related_name="improvement_actions")
    academic_year = models.CharField(max_length=20, default="2024-2025")
    outcome_type = models.CharField(max_length=10, choices=[("PO", "PO"), ("PSO", "PSO")])
    outcome_code = models.CharField(max_length=10)
    target_level = models.FloatField(default=2.5)  # Out of 3.0
    attained_level = models.FloatField(default=0.0)
    gap = models.FloatField(default=0.0)
    action_proposed = models.TextField()
    action_taken = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Proposed")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.gap = max(0.0, float(self.target_level) - float(self.attained_level))
        super(ContinuousImprovementAction, self).save(*args, **kwargs)

    def __str__(self):
        return f"Action on {self.outcome_code} ({self.academic_year}): Gap {self.gap:.2f}"


# ==============================================================================
# DOCUMENT MANAGEMENT & AUDITING
# ==============================================================================

class InstitutionalDocument(models.Model):
    CATEGORY_CHOICES = [
        ("Academic Calendar", "Academic Calendar"),
        ("Syllabus", "Syllabus"),
        ("Student Certificate", "Student Certificate"),
        ("Faculty Qualification", "Faculty Qualification"),
        ("Research Paper", "Research Paper"),
        ("Training Certificate", "Training Certificate"),
        ("Financial Receipt", "Financial Receipt"),
        ("Accreditation Evidence", "Accreditation Evidence"),
        ("Meeting Minutes", "Meeting Minutes"),
        ("Policy Document", "Policy Document"),
        ("Other", "Other"),
    ]

    title = models.CharField(max_length=250)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)
    file = models.FileField(upload_to="institutional_documents/")
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    academic_year = models.CharField(max_length=20, default="2024-2025")
    department = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_docs"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.category}] {self.title}"


class SystemAuditLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE, VERIFY, REOPEN, LOGIN
    module = models.CharField(max_length=100)
    description = models.TextField()
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.action}] {self.module} by {self.user} at {self.timestamp}"


# ==============================================================================
# POST SAVE SIGNALS FOR USER ROLES
# ==============================================================================

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        ut = str(instance.user_type)
        if ut == "1":
            Admin.objects.get_or_create(admin=instance)
        elif ut == "2":
            Staff.objects.get_or_create(admin=instance)
        elif ut == "3":
            Student.objects.get_or_create(admin=instance)
        elif ut == "4":
            Principal.objects.get_or_create(admin=instance)
        elif ut == "5":
            FinanceOfficer.objects.get_or_create(admin=instance)
        elif ut == "6":
            HROfficer.objects.get_or_create(admin=instance)
        elif ut == "7":
            AccreditationCoordinator.objects.get_or_create(admin=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    ut = str(instance.user_type)
    if ut == "1" and hasattr(instance, "admin"):
        instance.admin.save()
    elif ut == "2" and hasattr(instance, "staff"):
        instance.staff.save()
    elif ut == "3" and hasattr(instance, "student"):
        instance.student.save()
    elif ut == "4" and hasattr(instance, "principal"):
        instance.principal.save()
    elif ut == "5" and hasattr(instance, "financeofficer"):
        instance.financeofficer.save()
    elif ut == "6" and hasattr(instance, "hrofficer"):
        instance.hrofficer.save()
    elif ut == "7" and hasattr(instance, "accreditationcoordinator"):
        instance.accreditationcoordinator.save()
