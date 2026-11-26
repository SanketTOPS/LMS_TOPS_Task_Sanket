"""Idempotent database seed script for development and testing."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import sys
from pathlib import Path

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

# Ensure backend/ is on sys.path when invoked as `python -m app.seed` or `python app/seed.py`
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Assignment,
    Batch,
    BatchStatus,
    BatchStudent,
    Course,
    CourseModule,
    CourseStatus,
    Enrollment,
    EnrollmentStatus,
    Instructor,
    Lecture,
    Payment,
    PaymentStatus,
    Question,
    Quiz,
    QuizOption,
    Role,
    User,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEMO_PASSWORD = "Password@123"


def get_or_create_role(db: Session, name: str, description: str) -> Role:
    role = db.scalar(select(Role).where(Role.name == name))
    if role:
        return role
    role = Role(name=name, description=description)
    db.add(role)
    db.flush()
    return role


def get_or_create_user(
    db: Session,
    *,
    role: Role,
    full_name: str,
    email: str,
    phone: str,
    password_hash: str,
) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(
        role_id=role.id,
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        phone=phone,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def seed_database(db: Session) -> None:
    """Populate initial synthetic dataset idempotently."""
    hashed_pw = pwd_context.hash(DEMO_PASSWORD)

    # 1. Roles
    admin_role = get_or_create_role(db, "Admin", "Institute administrator with full access")
    instructor_role = get_or_create_role(db, "Instructor", "Course and batch instructor")
    student_role = get_or_create_role(db, "Student", "Enrolled learner")

    # 2. Users: 1 Admin, 2 Instructors, 5 Students
    admin = get_or_create_user(
        db,
        role=admin_role,
        full_name="Aarav Mehta",
        email="admin@institute.edu",
        phone="+91-9000000001",
        password_hash=hashed_pw,
    )

    inst_user_1 = get_or_create_user(
        db,
        role=instructor_role,
        full_name="Ananya Sharma",
        email="ananya.sharma@institute.edu",
        phone="+91-9000000002",
        password_hash=hashed_pw,
    )
    inst_user_2 = get_or_create_user(
        db,
        role=instructor_role,
        full_name="Rohan Verma",
        email="rohan.verma@institute.edu",
        phone="+91-9000000003",
        password_hash=hashed_pw,
    )

    instructor_specs = [
        (inst_user_1, "Full-stack web architect", "React, FastAPI, MySQL", "M.Tech CS", 7),
        (inst_user_2, "Applied ML & Python trainer", "Python, Data Science, SQL", "M.Sc Data Science", 5),
    ]
    instructors: list[Instructor] = []
    for u, bio, expertise, qual, exp in instructor_specs:
        inst = db.scalar(select(Instructor).where(Instructor.user_id == u.id))
        if not inst:
            inst = Instructor(
                user_id=u.id,
                bio=bio,
                expertise=expertise,
                qualification=qual,
                experience_years=exp,
                is_active=True,
            )
            db.add(inst)
            db.flush()
        instructors.append(inst)

    student_names = [
        ("Priya Nair", "student1@institute.edu", "+91-9000000101"),
        ("Kabir Patel", "student2@institute.edu", "+91-9000000102"),
        ("Sneha Iyer", "student3@institute.edu", "+91-9000000103"),
        ("Vikram Rao", "student4@institute.edu", "+91-9000000104"),
        ("Meera Joshi", "student5@institute.edu", "+91-9000000105"),
    ]
    students: list[User] = [
        get_or_create_user(
            db,
            role=student_role,
            full_name=name,
            email=email,
            phone=phone,
            password_hash=hashed_pw,
        )
        for name, email, phone in student_names
    ]

    # 3. 2 Courses with Modules
    course_1 = db.scalar(select(Course).where(Course.code == "FSWD-101"))
    if not course_1:
        course_1 = Course(
            title="Full-Stack Web Development",
            code="FSWD-101",
            description="End-to-end web engineering with React, FastAPI, and MySQL.",
            duration_weeks=12,
            fee_amount=Decimal("25000.00"),
            status=CourseStatus.PUBLISHED,
            created_by=admin.id,
        )
        db.add(course_1)
        db.flush()

    course_2 = db.scalar(select(Course).where(Course.code == "DSPY-201"))
    if not course_2:
        course_2 = Course(
            title="Data Science with Python",
            code="DSPY-201",
            description="Data analysis, visualization, and machine learning foundations.",
            duration_weeks=10,
            fee_amount=Decimal("22000.00"),
            status=CourseStatus.PUBLISHED,
            created_by=admin.id,
        )
        db.add(course_2)
        db.flush()

    c1_modules_data = [
        ("Module 1: Web & HTTP Fundamentals", "REST APIs, JSON, and client-server architecture", 1),
        ("Module 2: Backend with FastAPI & SQLAlchemy", "Routing, Pydantic schemas, ORM models", 2),
        ("Module 3: Frontend with React & Tailwind", "Components, hooks, and API integration", 3),
    ]
    c1_modules: list[CourseModule] = []
    for title, desc, order in c1_modules_data:
        mod = db.scalar(
            select(CourseModule).where(
                CourseModule.course_id == course_1.id,
                CourseModule.sort_order == order,
            )
        )
        if not mod:
            mod = CourseModule(
                course_id=course_1.id,
                title=title,
                description=desc,
                sort_order=order,
            )
            db.add(mod)
            db.flush()
        c1_modules.append(mod)

    c2_modules_data = [
        ("Module 1: Python & NumPy Essentials", "Data structures and vectorized operations", 1),
        ("Module 2: Data Wrangling with Pandas", "Cleaning, grouping, and merging datasets", 2),
    ]
    for title, desc, order in c2_modules_data:
        mod = db.scalar(
            select(CourseModule).where(
                CourseModule.course_id == course_2.id,
                CourseModule.sort_order == order,
            )
        )
        if not mod:
            mod = CourseModule(
                course_id=course_2.id,
                title=title,
                description=desc,
                sort_order=order,
            )
            db.add(mod)
            db.flush()

    # 4. 2 Batches
    batch_1 = db.scalar(select(Batch).where(Batch.code == "FSWD-2026-B1"))
    if not batch_1:
        batch_1 = Batch(
            course_id=course_1.id,
            instructor_id=instructors[0].id,
            name="FSWD Morning Batch 1",
            code="FSWD-2026-B1",
            start_date=date(2026, 11, 1),
            end_date=date(2027, 1, 24),
            schedule_info="Mon-Fri 09:00-11:00 IST",
            max_students=30,
            status=BatchStatus.ACTIVE,
        )
        db.add(batch_1)
        db.flush()

    batch_2 = db.scalar(select(Batch).where(Batch.code == "DSPY-2026-B1"))
    if not batch_2:
        batch_2 = Batch(
            course_id=course_2.id,
            instructor_id=instructors[1].id,
            name="DSPY Evening Batch 1",
            code="DSPY-2026-B1",
            start_date=date(2026, 11, 15),
            end_date=date(2027, 1, 30),
            schedule_info="Mon-Wed-Fri 18:00-20:00 IST",
            max_students=25,
            status=BatchStatus.ACTIVE,
        )
        db.add(batch_2)
        db.flush()

    # 5. Enrollments & BatchStudents
    enrollment_specs = [
        (students[0], course_1, batch_1),
        (students[1], course_1, batch_1),
        (students[2], course_1, batch_1),
        (students[3], course_2, batch_2),
        (students[4], course_2, batch_2),
    ]
    enrollments: list[Enrollment] = []
    for student, course, batch in enrollment_specs:
        enr = db.scalar(
            select(Enrollment).where(
                Enrollment.student_id == student.id,
                Enrollment.course_id == course.id,
            )
        )
        if not enr:
            enr = Enrollment(
                student_id=student.id,
                course_id=course.id,
                batch_id=batch.id,
                status=EnrollmentStatus.ACTIVE,
            )
            db.add(enr)
            db.flush()
        enrollments.append(enr)

        bs = db.scalar(
            select(BatchStudent).where(
                BatchStudent.batch_id == batch.id,
                BatchStudent.student_id == student.id,
            )
        )
        if not bs:
            bs = BatchStudent(batch_id=batch.id, student_id=student.id, is_active=True)
            db.add(bs)

    # 6. 1 Lecture
    lecture_1 = db.scalar(
        select(Lecture).where(
            Lecture.module_id == c1_modules[0].id,
            Lecture.title == "Introduction to RESTful APIs",
        )
    )
    if not lecture_1:
        lecture_1 = Lecture(
            module_id=c1_modules[0].id,
            batch_id=batch_1.id,
            title="Introduction to RESTful APIs",
            description="Overview of HTTP verbs, status codes, and stateless API design.",
            video_url="https://example.edu/videos/fswd-lecture-1.mp4",
            duration_minutes=45,
            sort_order=1,
            is_published=True,
            created_by=inst_user_1.id,
        )
        db.add(lecture_1)
        db.flush()

    # 7. 1 Assignment
    assignment_1 = db.scalar(
        select(Assignment).where(
            Assignment.course_id == course_1.id,
            Assignment.title == "Build a REST Resource Specification",
        )
    )
    if not assignment_1:
        assignment_1 = Assignment(
            course_id=course_1.id,
            batch_id=batch_1.id,
            module_id=c1_modules[0].id,
            title="Build a REST Resource Specification",
            description="Document 5 REST endpoints with request/response JSON examples.",
            max_marks=Decimal("100.00"),
            due_date=datetime.now(timezone.utc) + timedelta(days=7),
            allow_late=True,
            created_by=inst_user_1.id,
        )
        db.add(assignment_1)
        db.flush()

    # 8. 1 Quiz with 5 MCQs
    quiz_1 = db.scalar(
        select(Quiz).where(
            Quiz.course_id == course_1.id,
            Quiz.title == "HTTP & REST Fundamentals Quiz",
        )
    )
    if not quiz_1:
        quiz_1 = Quiz(
            course_id=course_1.id,
            batch_id=batch_1.id,
            title="HTTP & REST Fundamentals Quiz",
            description="5-question check on HTTP methods and status codes.",
            time_limit_minutes=15,
            passing_marks=Decimal("3.00"),
            total_marks=Decimal("5.00"),
            allow_retake=False,
            max_attempts=1,
            is_published=True,
            created_by=inst_user_1.id,
        )
        db.add(quiz_1)
        db.flush()

        mcq_specs = [
            (
                "Which HTTP status code indicates a resource was successfully created?",
                ["200 OK", "201 Created", "204 No Content", "400 Bad Request"],
                1,
            ),
            (
                "Which HTTP method is idempotent and used to replace a resource?",
                ["POST", "PUT", "CONNECT", "TRACE"],
                1,
            ),
            (
                "Which status code indicates the user is authenticated but lacks permission?",
                ["401 Unauthorized", "403 Forbidden", "404 Not Found", "409 Conflict"],
                1,
            ),
            (
                "What does the 409 Conflict status code typically represent?",
                ["Server crash", "Duplicate or conflicting state", "Invalid JSON syntax", "Timeout"],
                1,
            ),
            (
                "Which header is commonly used to carry a JWT bearer token?",
                ["X-Custom-Token", "Authorization", "Content-Type", "Accept"],
                1,
            ),
        ]

        for q_idx, (q_text, opts, correct_idx) in enumerate(mcq_specs, start=1):
            question = Question(
                quiz_id=quiz_1.id,
                question_text=q_text,
                marks=Decimal("1.00"),
                sort_order=q_idx,
            )
            db.add(question)
            db.flush()

            created_options: list[QuizOption] = []
            for o_idx, opt_text in enumerate(opts, start=1):
                option = QuizOption(
                    question_id=question.id,
                    option_text=opt_text,
                    sort_order=o_idx,
                )
                db.add(option)
                db.flush()
                created_options.append(option)

            question.correct_option_id = created_options[correct_idx].id
            db.flush()

    # 9. Payments
    payment_specs = [
        (students[0], course_1, enrollments[0], Decimal("25000.00"), Decimal("25000.00"), "UPI", "TXN-1001", PaymentStatus.PAID),
        (students[1], course_1, enrollments[1], Decimal("25000.00"), Decimal("12500.00"), "Card", "TXN-1002", PaymentStatus.PARTIALLY_PAID),
        (students[3], course_2, enrollments[3], Decimal("22000.00"), Decimal("0.00"), None, "TXN-1003", PaymentStatus.PENDING),
    ]
    for student, course, enr, due, paid, method, ref, status in payment_specs:
        existing_payment = db.scalar(select(Payment).where(Payment.transaction_ref == ref))
        if not existing_payment:
            payment = Payment(
                student_id=student.id,
                course_id=course.id,
                enrollment_id=enr.id,
                amount_due=due,
                amount_paid=paid,
                payment_method=method,
                transaction_ref=ref,
                status=status,
                paid_at=datetime.now(timezone.utc) if paid > 0 else None,
                recorded_by=admin.id,
                notes="Initial seeded payment record",
            )
            db.add(payment)

    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed_database(db)

    print("Database seeded successfully.")
    print("Demo credentials (all accounts use the same synthetic password):")
    print(f"  Password   : {DEMO_PASSWORD}")
    print("  Admin      : admin@institute.edu")
    print("  Instructors: ananya.sharma@institute.edu, rohan.verma@institute.edu")
    print("  Students   : student1@institute.edu .. student5@institute.edu")


if __name__ == "__main__":
    main()
