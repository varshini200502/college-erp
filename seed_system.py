import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from main_app.models import (
    CustomUser, Admin, Staff, Student, Principal, FinanceOfficer, HROfficer,
    AccreditationCoordinator, Course, Session, Subject,
    FeeStructure, StudentFeeAccount,
    NAACCriterion, NBAProgram, ProgramOutcome
)

User = get_user_model()

def seed_users():
    print("--- Seeding Users for 6 Primary Roles ---")
    roles = [
        ("admin@admin.com", "admin123", "1", "System", "Administrator"),
        ("staffone@staff.com", "staff123", "2", "Alan", "Turing"),
        ("studentone@student.com", "student123", "3", "Grace", "Hopper"),
        ("principal@college.edu", "principal123", "4", "Dr. Robert", "Oppenheimer"),
        ("finance@college.edu", "finance123", "5", "Warren", "Buffett"),
        ("accreditation@college.edu", "accreditation123", "7", "Dr. Margaret", "Hamilton"),
    ]

    for email, pwd, role_num, first_name, last_name in roles:
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(
                email=email,
                password=pwd,
                user_type=role_num,
                first_name=first_name,
                last_name=last_name
            )
            print(f"[CREATED] {email} (Role {role_num})")
        else:
            user.set_password(pwd)
            user.user_type = role_num
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True
            user.save()
            print(f"[UPDATED] {email} (Role {role_num})")

        # Verify corresponding profile exists
        if role_num == '1':
            Admin.objects.get_or_create(admin=user)
        elif role_num == '2':
            s, _ = Staff.objects.get_or_create(admin=user)
            if not s.course:
                s.course = Course.objects.first()
                s.save()
        elif role_num == '3':
            st, _ = Student.objects.get_or_create(admin=user)
            if not st.course:
                st.course = Course.objects.first()
            if not st.session:
                st.session = Session.objects.first()
            st.roll_number = st.roll_number or f"STU-{st.id:04d}"
            st.current_semester = st.current_semester or 4
            st.save()
        elif role_num == '4':
            Principal.objects.get_or_create(admin=user)
        elif role_num == '5':
            FinanceOfficer.objects.get_or_create(admin=user)
        elif role_num == '6':
            HROfficer.objects.get_or_create(admin=user)
        elif role_num == '7':
            AccreditationCoordinator.objects.get_or_create(admin=user)

def seed_naac():
    print("\n--- Seeding 7 NAAC Criteria ---")
    standard_criteria = [
        (1, "Curricular Aspects", 100, "Curricular planning, academic flexibility, curriculum enrichment, and feedback systems."),
        (2, "Teaching-Learning and Evaluation", 350, "Student enrollment, diversity, student-teacher ratio, teaching methods, and evaluation processes."),
        (3, "Research, Innovations and Extension", 110, "Resource mobilization, innovation ecosystem, research publications, patents, and extension activities."),
        (4, "Infrastructure and Learning Resources", 100, "Physical facilities, library as a learning resource, IT infrastructure, and campus maintenance."),
        (5, "Student Support and Progression", 140, "Student mentoring, scholarships, capacity building, student placement, and alumni engagement."),
        (6, "Governance, Leadership and Management", 100, "Institutional vision, strategy, faculty empowerment, financial management, and IQAC quality assurance."),
        (7, "Institutional Values and Best Practices", 100, "Institutional values, gender equity, environmental consciousness, best practices, and distinctiveness."),
    ]
    for num, name, weight, desc in standard_criteria:
        c, created = NAACCriterion.objects.get_or_create(
            criterion_number=num,
            defaults={'name': name, 'weightage': weight, 'description': desc}
        )
        if created:
            print(f"[CREATED] NAAC Criterion {num}: {name}")
        else:
            print(f"[EXISTS] NAAC Criterion {num}: {name}")

def seed_nba():
    print("\n--- Seeding NBA Program & POs ---")
    course = Course.objects.first()
    if not course:
        course = Course.objects.create(name="Computer Science & Engineering")
        print("[CREATED] Course: Computer Science & Engineering")

    program, created = NBAProgram.objects.get_or_create(
        course=course,
        defaults={
            'program_name': f"B.Tech in {course.name}",
            'tier': 'Tier II'
        }
    )
    if created:
        print(f"[CREATED] NBA Program: {program.program_name}")
    else:
        print(f"[EXISTS] NBA Program: {program.program_name}")

    standard_pos = [
        ("PO1", "Engineering Knowledge", "Apply mathematics, science, engineering fundamentals, and an engineering specialization to the solution of complex engineering problems."),
        ("PO2", "Problem Analysis", "Identify, formulate, review research literature, and analyze complex engineering problems reaching substantiated conclusions."),
        ("PO3", "Design/Development of Solutions", "Design solutions for complex engineering problems and design system components or processes that meet the specified needs."),
        ("PO4", "Conduct Investigations of Complex Problems", "Use research-based knowledge and research methods including design of experiments, analysis and interpretation of data."),
        ("PO5", "Modern Tool Usage", "Create, select, and apply appropriate techniques, resources, and modern engineering and IT tools."),
        ("PO6", "The Engineer and Society", "Apply reasoning informed by contextual knowledge to assess societal, health, safety, legal and cultural issues."),
        ("PO7", "Environment and Sustainability", "Understand the impact of professional engineering solutions in societal and environmental contexts."),
        ("PO8", "Ethics", "Apply ethical principles and commit to professional ethics and responsibilities and norms of engineering practice."),
        ("PO9", "Individual and Team Work", "Function effectively as an individual, and as a member or leader in diverse teams, and in multidisciplinary settings."),
        ("PO10", "Communication", "Communicate effectively on complex engineering activities with the engineering community and with society at large."),
        ("PO11", "Project Management and Finance", "Demonstrate knowledge and understanding of engineering and management principles and apply these to one's own work."),
        ("PO12", "Life-long Learning", "Recognize the need for, and have the preparation and ability to engage in independent and life-long learning."),
    ]
    for code, title, desc in standard_pos:
        po, p_created = ProgramOutcome.objects.get_or_create(
            program=program,
            code=code,
            defaults={'title': title, 'description': desc}
        )
        if p_created:
            print(f"[CREATED] NBA PO: {code} - {title}")

def seed_finance():
    print("\n--- Seeding Finance Structures ---")
    course = Course.objects.first()
    session = Session.objects.first()
    fs, created = FeeStructure.objects.get_or_create(
        name="Standard Engineering Tuition & Labs 2024-25",
        course=course,
        academic_year="2024-2025",
        defaults={
            'session': session,
            'tuition_fee': 75000.0,
            'development_fee': 15000.0,
            'exam_fee': 5000.0,
            'lab_fee': 12000.0,
            'library_fee': 3000.0,
            'other_fee': 2000.0
        }
    )
    if created:
        print(f"[CREATED] FeeStructure: {fs.name} (Total: ₹{fs.total_fee})")
    else:
        print(f"[EXISTS] FeeStructure: {fs.name} (Total: ₹{fs.total_fee})")

    # Link to students
    for st in Student.objects.all():
        acc, a_created = StudentFeeAccount.objects.get_or_create(
            student=st,
            defaults={'fee_structure': fs}
        )
        acc.fee_structure = fs
        acc.recalculate()
        if a_created:
            print(f"[CREATED] Fee Account for student: {st}")

if __name__ == '__main__':
    seed_users()
    seed_naac()
    seed_nba()
    seed_finance()
    print("\n=== SYSTEM SEEDING COMPLETED SUCCESSFULLY ===")
