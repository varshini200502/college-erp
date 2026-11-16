"""
seed_demo_data.py – Comprehensive realistic demo data for College ERP.

Run: python seed_demo_data.py
Safe to re-run (uses get_or_create everywhere).
All demo records tagged with [DEMO] in notes/descriptions where applicable.
"""
import os, sys, django
from datetime import date, timedelta
import random

sys.path.insert(0, r'D:\College_ERP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
django.setup()

from main_app.models import (
    CustomUser, Admin, Staff, Student, Course, Subject, Session,
    Attendance, AttendanceReport, StudentResult, AlumniProfile,
    LeaveReportStaff, LeaveReportStudent,
)

print("=" * 60)
print("COLLEGE ERP – Comprehensive Demo Data Seeder")
print("=" * 60)

# ─────────────────────────────────────────────────────────────
# 1. COURSES (Departments)
# ─────────────────────────────────────────────────────────────
print("\n[1] Creating Courses / Departments...")
COURSES = [
    "Computer Science & Engineering",
    "Electronics & Communication Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Information Technology",
    "Electrical Engineering",
    "Artificial Intelligence & Data Science",
]
course_objs = {}
for c_name in COURSES:
    obj, created = Course.objects.get_or_create(name=c_name)
    course_objs[c_name] = obj
    print(f"  {'Created' if created else 'Exists '}: {c_name}")

# ─────────────────────────────────────────────────────────────
# 2. SESSIONS (Admission Batches)
# ─────────────────────────────────────────────────────────────
print("\n[2] Creating Academic Sessions...")
SESSIONS = [
    (date(2020, 7, 1), date(2024, 5, 31)),
    (date(2021, 7, 1), date(2025, 5, 31)),
    (date(2022, 7, 1), date(2026, 5, 31)),
    (date(2023, 7, 1), date(2027, 5, 31)),
    (date(2024, 7, 1), date(2028, 5, 31)),
]
session_objs = []
for start, end in SESSIONS:
    obj, created = Session.objects.get_or_create(start_year=start, end_year=end)
    session_objs.append(obj)
    print(f"  {'Created' if created else 'Exists '}: {obj}")

# ─────────────────────────────────────────────────────────────
# 3. FACULTY / STAFF (10 members)
# ─────────────────────────────────────────────────────────────
print("\n[3] Creating Faculty Members...")
FACULTY_DATA = [
    # (email, password, first, last, course_key, faculty_id, designation, dept, doj, qual, spec, exp)
    ("dr.sharma@college.edu", "faculty123", "Rajesh", "Sharma",
     "Computer Science & Engineering", "CSE-F001", "Professor",
     "CSE", date(2010, 7, 15), "Ph.D (Computer Science)", "Machine Learning", 14.0),
    ("dr.patel@college.edu", "faculty123", "Meena", "Patel",
     "Computer Science & Engineering", "CSE-F002", "Associate Professor",
     "CSE", date(2013, 8, 1), "Ph.D (Networks)", "Computer Networks", 11.0),
    ("dr.rao@college.edu", "faculty123", "Suresh", "Rao",
     "Electronics & Communication Engineering", "ECE-F001", "Professor",
     "ECE", date(2008, 6, 20), "Ph.D (VLSI)", "VLSI Design", 16.5),
    ("ms.kumar@college.edu", "faculty123", "Priya", "Kumar",
     "Mechanical Engineering", "MECH-F001", "Assistant Professor",
     "Mechanical", date(2017, 7, 1), "M.Tech (Thermal)", "Thermal Engineering", 7.0),
    ("dr.joshi@college.edu", "faculty123", "Anil", "Joshi",
     "Civil Engineering", "CIVIL-F001", "Associate Professor",
     "Civil", date(2012, 7, 10), "Ph.D (Structural)", "Structural Analysis", 12.0),
    ("mr.verma@college.edu", "faculty123", "Deepak", "Verma",
     "Information Technology", "IT-F001", "Assistant Professor",
     "IT", date(2019, 1, 15), "M.Tech (Software Engg)", "Web Technologies", 5.5),
    ("dr.nair@college.edu", "faculty123", "Lakshmi", "Nair",
     "Artificial Intelligence & Data Science", "AIDS-F001", "Professor",
     "AI&DS", date(2009, 7, 1), "Ph.D (AI)", "Deep Learning", 15.0),
    ("ms.singh@college.edu", "faculty123", "Kavita", "Singh",
     "Electrical Engineering", "EE-F001", "Assistant Professor",
     "Electrical", date(2020, 8, 1), "M.Tech (Power Systems)", "Power Electronics", 4.0),
    ("dr.mehta@college.edu", "faculty123", "Ravi", "Mehta",
     "Computer Science & Engineering", "CSE-F003", "Assistant Professor",
     "CSE", date(2016, 7, 1), "Ph.D (Algorithms)", "Data Structures & Algorithms", 8.5),
    ("ms.reddy@college.edu", "faculty123", "Ananya", "Reddy",
     "Artificial Intelligence & Data Science", "AIDS-F002", "Assistant Professor",
     "AI&DS", date(2021, 7, 1), "M.Tech (Data Science)", "Data Analytics", 3.5),
]

staff_objs = []
for (email, pwd, fname, lname, course_key, fac_id, desig, dept,
     doj, qual, spec, exp) in FACULTY_DATA:
    user_exists = CustomUser.objects.filter(email=email).first()
    if user_exists:
        print(f"  Exists : {fname} {lname} ({email})")
        staff_objs.append(user_exists.staff)
        continue
    try:
        user = CustomUser.objects.create_user(
            email=email, password=pwd, user_type=2,
            first_name=fname, last_name=lname, profile_pic='')
        user.gender = random.choice(['M', 'F'])
        user.address = f"[DEMO] {random.randint(1, 100)}, College Staff Quarters, Main Campus"
        user.save()
        staff = user.staff
        staff.course = course_objs[course_key]
        staff.faculty_id = fac_id
        staff.designation = desig
        staff.department = dept
        staff.date_of_joining = doj
        staff.employment_status = 'Active'
        staff.total_experience_years = exp
        staff.highest_qualification = qual
        staff.specialization = spec
        staff.save()
        staff_objs.append(staff)
        print(f"  Created: {fname} {lname} – {desig} ({course_key})")
    except Exception as e:
        print(f"  ERROR creating {fname} {lname}: {e}")

# ─────────────────────────────────────────────────────────────
# 4. SUBJECTS (3–4 per course)
# ─────────────────────────────────────────────────────────────
print("\n[4] Creating Subjects...")
SUBJECTS_DATA = [
    # (name, course_key, staff_email)
    ("Data Structures & Algorithms",          "Computer Science & Engineering",          "dr.sharma@college.edu"),
    ("Database Management Systems",           "Computer Science & Engineering",          "dr.patel@college.edu"),
    ("Operating Systems",                     "Computer Science & Engineering",          "dr.mehta@college.edu"),
    ("Computer Networks",                     "Computer Science & Engineering",          "dr.patel@college.edu"),
    ("Software Engineering",                  "Computer Science & Engineering",          "mr.verma@college.edu"),

    ("Digital Electronics",                   "Electronics & Communication Engineering", "dr.rao@college.edu"),
    ("Signals & Systems",                     "Electronics & Communication Engineering", "dr.rao@college.edu"),
    ("Microprocessors",                       "Electronics & Communication Engineering", "dr.rao@college.edu"),

    ("Engineering Mechanics",                 "Mechanical Engineering",                  "ms.kumar@college.edu"),
    ("Thermodynamics",                        "Mechanical Engineering",                  "ms.kumar@college.edu"),
    ("Manufacturing Processes",               "Mechanical Engineering",                  "ms.kumar@college.edu"),

    ("Structural Analysis",                   "Civil Engineering",                       "dr.joshi@college.edu"),
    ("Fluid Mechanics",                       "Civil Engineering",                       "dr.joshi@college.edu"),
    ("Surveying",                             "Civil Engineering",                       "dr.joshi@college.edu"),

    ("Web Technologies",                      "Information Technology",                  "mr.verma@college.edu"),
    ("Cloud Computing",                       "Information Technology",                  "mr.verma@college.edu"),
    ("Information Security",                  "Information Technology",                  "dr.patel@college.edu"),

    ("Power Systems",                         "Electrical Engineering",                  "ms.singh@college.edu"),
    ("Control Systems",                       "Electrical Engineering",                  "ms.singh@college.edu"),
    ("Electrical Machines",                   "Electrical Engineering",                  "ms.singh@college.edu"),

    ("Machine Learning",                      "Artificial Intelligence & Data Science",  "dr.nair@college.edu"),
    ("Deep Learning",                         "Artificial Intelligence & Data Science",  "dr.nair@college.edu"),
    ("Data Analytics & Visualization",        "Artificial Intelligence & Data Science",  "ms.reddy@college.edu"),
    ("Natural Language Processing",           "Artificial Intelligence & Data Science",  "dr.nair@college.edu"),
]
subject_objs = []
for subj_name, course_key, staff_email in SUBJECTS_DATA:
    course = course_objs[course_key]
    staff_user = CustomUser.objects.filter(email=staff_email).first()
    if not staff_user:
        print(f"  SKIP (staff not found): {subj_name}")
        continue
    staff = staff_user.staff
    obj, created = Subject.objects.get_or_create(
        name=subj_name, course=course,
        defaults={'staff': staff}
    )
    if not created:
        # update staff assignment
        obj.staff = staff
        obj.save()
    subject_objs.append(obj)
    print(f"  {'Created' if created else 'Exists '}: {subj_name} ({course_key[:20]})")

# ─────────────────────────────────────────────────────────────
# 5. STUDENTS (20 students across courses and sessions)
# ─────────────────────────────────────────────────────────────
print("\n[5] Creating Students...")
STUDENT_DATA = [
    # (email, pwd, first, last, course_key, session_idx, roll, adm_no, dob, phone, parent, status, sem, section)
    ("aryan.kapoor@student.edu",   "student123", "Aryan",    "Kapoor",    "Computer Science & Engineering",          0, "CSE20001", "ADM20001", date(2002,3,15),  "9876543201", "Rajiv Kapoor",    "Active",  7, "A"),
    ("sneha.gupta@student.edu",    "student123", "Sneha",    "Gupta",     "Computer Science & Engineering",          0, "CSE20002", "ADM20002", date(2002,6,22),  "9876543202", "Pradeep Gupta",   "Alumni",  8, "A"),
    ("rahul.mishra@student.edu",   "student123", "Rahul",    "Mishra",    "Electronics & Communication Engineering", 1, "ECE21001", "ADM21001", date(2003,1,10),  "9876543203", "Sunil Mishra",    "Active",  5, "B"),
    ("pooja.shah@student.edu",     "student123", "Pooja",    "Shah",      "Computer Science & Engineering",          1, "CSE21001", "ADM21003", date(2003,4,18),  "9876543204", "Amit Shah",       "Active",  5, "A"),
    ("vikram.nair@student.edu",    "student123", "Vikram",   "Nair",      "Mechanical Engineering",                  1, "MECH21001","ADM21004", date(2003,7,25),  "9876543205", "Kumar Nair",      "Active",  5, "A"),
    ("isha.verma@student.edu",     "student123", "Isha",     "Verma",     "Information Technology",                  2, "IT22001",  "ADM22001", date(2004,2,12),  "9876543206", "Deepak Verma",    "Active",  3, "A"),
    ("karthik.raj@student.edu",    "student123", "Karthik",  "Raj",       "Artificial Intelligence & Data Science",  2, "AIDS22001","ADM22002", date(2004,5,8),   "9876543207", "Suresh Raj",      "Active",  3, "B"),
    ("meera.joshi@student.edu",    "student123", "Meera",    "Joshi",     "Civil Engineering",                       2, "CIVIL22001","ADM22003",date(2004,8,30),  "9876543208", "Anil Joshi",      "Active",  3, "A"),
    ("rohan.patel@student.edu",    "student123", "Rohan",    "Patel",     "Electrical Engineering",                  2, "EE22001",  "ADM22004", date(2004,11,5),  "9876543209", "Bhavesh Patel",   "Active",  3, "A"),
    ("divya.kumar@student.edu",    "student123", "Divya",    "Kumar",     "Computer Science & Engineering",          2, "CSE22001", "ADM22005", date(2004,3,20),  "9876543210", "Ramesh Kumar",    "Active",  3, "B"),
    ("aditya.singh@student.edu",   "student123", "Aditya",   "Singh",     "Computer Science & Engineering",          3, "CSE23001", "ADM23001", date(2005,1,14),  "9876543211", "Harpreet Singh",  "Active",  1, "A"),
    ("priyanka.rao@student.edu",   "student123", "Priyanka", "Rao",       "Electronics & Communication Engineering", 3, "ECE23001", "ADM23002", date(2005,4,25),  "9876543212", "Venkat Rao",      "Active",  1, "A"),
    ("siddharth.jain@student.edu", "student123", "Siddharth","Jain",      "Mechanical Engineering",                  3, "MECH23001","ADM23003", date(2005,6,10),  "9876543213", "Suresh Jain",     "Active",  1, "B"),
    ("nisha.reddy@student.edu",    "student123", "Nisha",    "Reddy",     "Artificial Intelligence & Data Science",  3, "AIDS23001","ADM23004", date(2005,9,3),   "9876543214", "Ravi Reddy",      "Active",  1, "A"),
    ("ankur.sharma@student.edu",   "student123", "Ankur",    "Sharma",    "Civil Engineering",                       3, "CIVIL23001","ADM23005",date(2005,2,28),  "9876543215", "Ramesh Sharma",   "Active",  1, "A"),
    # Alumni (batch 2020)
    ("alum.raj@alumni.edu",        "alumni123",  "Sumanth",  "Raj",       "Computer Science & Engineering",          0, "CSE20010", "ADM20010", date(2001,8,12),  "9876543216", "Krishna Raj",     "Alumni",  8, "A"),
    ("alum.priya@alumni.edu",      "alumni123",  "Priya",    "Sharma",    "Electronics & Communication Engineering", 0, "ECE20011", "ADM20011", date(2001,5,20),  "9876543217", "Mahesh Sharma",   "Alumni",  8, "A"),
    ("alum.anand@alumni.edu",      "alumni123",  "Anand",    "Krishnan",  "Mechanical Engineering",                  0, "MECH20012","ADM20012", date(2001,3,8),   "9876543218", "Sundaram Krishnan","Alumni", 8, "A"),
    ("alum.sara@alumni.edu",       "alumni123",  "Sara",     "Thomas",    "Information Technology",                  0, "IT20013",  "ADM20013", date(2001,11,15), "9876543219", "John Thomas",     "Alumni",  8, "A"),
    ("alum.rahul2@alumni.edu",     "alumni123",  "Rahul",    "Desai",     "Artificial Intelligence & Data Science",  1, "AIDS21014","ADM21014", date(2002,7,22),  "9876543220", "Nilesh Desai",    "Graduated",8,"B"),
]

student_objs = []
for (email, pwd, fname, lname, course_key, sess_idx, roll, adm_no,
     dob, phone, parent, status, sem, section) in STUDENT_DATA:
    existing = CustomUser.objects.filter(email=email).first()
    if existing:
        print(f"  Exists : {fname} {lname} ({email})")
        student_objs.append(existing.student)
        continue
    try:
        user = CustomUser.objects.create_user(
            email=email, password=pwd, user_type=3,
            first_name=fname, last_name=lname, profile_pic='')
        user.gender = random.choice(['M', 'F'])
        user.address = f"[DEMO] {random.randint(1, 200)}, Student Hostel / Local Address, Campus City"
        user.save()
        student = user.student
        student.course = course_objs[course_key]
        student.session = session_objs[sess_idx]
        student.roll_number = roll
        student.admission_number = adm_no
        student.date_of_birth = dob
        student.phone = phone
        student.parent_name = parent
        student.parent_phone = f"91{random.randint(6000000000, 9999999999)}"
        student.status = status
        student.current_semester = sem
        student.section = section
        student.sgpa = round(random.uniform(6.5, 9.5), 2)
        student.cgpa = round(random.uniform(6.0, 9.0), 2)
        student.save()
        student_objs.append(student)
        print(f"  Created: {fname} {lname} – {course_key[:25]} (Sem {sem}, {status})")
    except Exception as e:
        print(f"  ERROR creating {fname} {lname}: {e}")

# ─────────────────────────────────────────────────────────────
# 6. ALUMNI PROFILES for Alumni/Graduated students
# ─────────────────────────────────────────────────────────────
print("\n[6] Creating Alumni Profiles...")
ALUMNI_EXTRAS = {
    "sneha.gupta@student.edu":   ("Google India", "Software Engineer", "Bangalore", "https://linkedin.com/in/snehagupta", 2024, "B.Tech CSE", "", "", False),
    "alum.raj@alumni.edu":       ("Microsoft", "Senior Software Engineer", "Hyderabad", "https://linkedin.com/in/sumanthraj", 2024, "B.Tech CSE", "IIT Delhi", "M.Tech CS", True),
    "alum.priya@alumni.edu":     ("Samsung R&D", "RF Engineer", "Noida", "https://linkedin.com/in/priyasharma", 2024, "B.Tech ECE", "", "", False),
    "alum.anand@alumni.edu":     ("Tata Motors", "Design Engineer", "Pune", "", 2024, "B.Tech Mechanical", "", "", False),
    "alum.sara@alumni.edu":      ("Infosys", "Systems Engineer", "Chennai", "https://linkedin.com/in/sarathomas", 2024, "B.Tech IT", "IIM Ahmedabad", "MBA", True),
    "alum.rahul2@alumni.edu":    ("Amazon", "Data Scientist", "Mumbai", "https://linkedin.com/in/rahuldesai", 2025, "B.Tech AI&DS", "", "", True),
}
for email, (company, desig, city, linkedin, grad_yr, degree, he_inst, he_degree, notable) in ALUMNI_EXTRAS.items():
    user = CustomUser.objects.filter(email=email).first()
    if not user:
        print(f"  SKIP (user not found): {email}")
        continue
    student = user.student
    alumni, created = AlumniProfile.objects.get_or_create(student=student)
    alumni.current_company = company
    alumni.current_designation = desig
    alumni.current_city = city
    alumni.linkedin_url = linkedin or None
    alumni.graduation_year = grad_yr
    alumni.degree_awarded = degree
    alumni.higher_education_institution = he_inst
    alumni.higher_education_degree = he_degree
    alumni.is_notable = notable
    alumni.engagement_notes = "[DEMO] Profile created by demo data seeder."
    alumni.save()
    print(f"  {'Created' if created else 'Updated'}: Alumni profile for {user.get_full_name()} → {company}")

# ─────────────────────────────────────────────────────────────
# 7. ATTENDANCE RECORDS (last 30 days for active students)
# ─────────────────────────────────────────────────────────────
print("\n[7] Creating Attendance Records (last 30 days)...")
today = date.today()
active_students = Student.objects.filter(status='Active').select_related('course', 'admin')

created_att = 0
for student in active_students:
    # Get subjects for student's course
    course_subjects = Subject.objects.filter(course=student.course)[:3]  # First 3 subjects
    for subject in course_subjects:
        # Create attendance for 30 working days (skip weekends roughly)
        for days_ago in range(1, 31):
            att_date = today - timedelta(days=days_ago)
            if att_date.weekday() >= 5:  # Skip Saturday/Sunday
                continue
            # Random attendance ~85% present
            is_present = random.random() < 0.85
            att, att_created = Attendance.objects.get_or_create(
                subject=subject,
                date=att_date,
                defaults={'session': student.session}
            )
            report, r_created = AttendanceReport.objects.get_or_create(
                student=student,
                attendance=att,
                defaults={'status': is_present}
            )
            if r_created:
                created_att += 1

print(f"  Created {created_att} attendance report entries.")

# ─────────────────────────────────────────────────────────────
# 8. STUDENT RESULTS (Marks)
# ─────────────────────────────────────────────────────────────
print("\n[8] Creating Student Result Records...")
created_results = 0
for student in Student.objects.filter(status='Active').select_related('course', 'session'):
    course_subjects = Subject.objects.filter(course=student.course)[:4]
    for subject in course_subjects:
        _, created = StudentResult.objects.get_or_create(
            student=student,
            subject=subject,
            defaults={
                'test': round(random.uniform(12, 25), 1),
                'exam': round(random.uniform(45, 95), 1),
                'assignment': round(random.uniform(5, 10), 1),
                'practical': round(random.uniform(0, 25), 1),
            }
        )
        if created:
            # Compute total
            obj = StudentResult.objects.get(student=student, subject=subject)
            obj.total = obj.test + obj.exam + obj.assignment + obj.practical
            obj.save()
            created_results += 1

# Results for alumni too
for student in Student.objects.filter(status__in=['Alumni', 'Graduated']).select_related('course', 'session'):
    course_subjects = Subject.objects.filter(course=student.course)[:5]
    for subject in course_subjects:
        _, created = StudentResult.objects.get_or_create(
            student=student,
            subject=subject,
            defaults={
                'test': round(random.uniform(15, 25), 1),
                'exam': round(random.uniform(55, 98), 1),
                'assignment': round(random.uniform(7, 10), 1),
                'practical': round(random.uniform(10, 25), 1),
            }
        )
        if created:
            obj = StudentResult.objects.get(student=student, subject=subject)
            obj.total = obj.test + obj.exam + obj.assignment + obj.practical
            obj.save()
            created_results += 1

print(f"  Created {created_results} student result records.")

# ─────────────────────────────────────────────────────────────
# 9. PRINT FINAL SUMMARY
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("DEMO DATA SEED COMPLETE — SUMMARY")
print("=" * 60)
print(f"  Courses:         {Course.objects.count()}")
print(f"  Sessions:        {Session.objects.count()}")
print(f"  Faculty (Staff): {CustomUser.objects.filter(user_type=2).count()}")
print(f"  Students:        {CustomUser.objects.filter(user_type=3).count()}")
print(f"    Active:        {Student.objects.filter(status='Active').count()}")
print(f"    Alumni:        {Student.objects.filter(status='Alumni').count()}")
print(f"    Graduated:     {Student.objects.filter(status='Graduated').count()}")
print(f"  Alumni Profiles: {AlumniProfile.objects.count()}")
print(f"  Subjects:        {Subject.objects.count()}")
print(f"  Attendance:      {Attendance.objects.count()} sessions")
print(f"  Att. Reports:    {AttendanceReport.objects.count()} records")
print(f"  Results:         {StudentResult.objects.count()} records")
print()
print("Demo credentials:")
print("  Admin:         admin@admin.com / admin123")
print("  Principal:     principal@college.edu / principal123")
print("  Faculty:       dr.sharma@college.edu / faculty123")
print("  Student:       aryan.kapoor@student.edu / student123")
print("  Finance:       finance@college.edu / finance123")
print("  Accreditation: accreditation@college.edu / accreditation123")
print()
print("Run: python manage.py runserver to start the application.")
