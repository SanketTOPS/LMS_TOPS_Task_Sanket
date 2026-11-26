from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Assignment,
    Attendance,
    AttendanceStatus,
    Base,
    Batch,
    BatchStatus,
    BatchStudent,
    ClassSession,
    ClassSessionStatus,
    Course,
    CourseModule,
    CourseStatus,
    Enrollment,
    EnrollmentStatus,
    Instructor,
    Lecture,
    LectureProgress,
    Question,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizOption,
    Role,
    Submission,
    SubmissionStatus,
    User,
)
from app.utils.limiter import limiter  # noqa: E402
from app.utils.security import hash_password  # noqa: E402


@pytest.fixture()
def pay_ctx():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    admin_role = Role(name="Admin", description="Admin")
    inst_role = Role(name="Instructor", description="Instructor")
    stu_role = Role(name="Student", description="Student")
    db.add_all([admin_role, inst_role, stu_role])
    db.flush()

    pw = hash_password("Password@123")
    admin = User(role_id=admin_role.id, full_name="Admin Admin", email="admin@test.edu", password_hash=pw, is_active=True)
    inst_u = User(role_id=inst_role.id, full_name="Prof Inst", email="inst@test.edu", password_hash=pw, is_active=True)
    stu = User(role_id=stu_role.id, full_name="Alice Student", email="alice@test.edu", password_hash=pw, is_active=True)
    db.add_all([admin, inst_u, stu])
    db.flush()

    instructor = Instructor(user_id=inst_u.id, expertise="Web Dev")
    db.add(instructor)
    db.flush()

    course = Course(
        title="Fullstack Web Development",
        code="CS-501",
        description="Comprehensive Bootcamp",
        fee_amount=Decimal("1000.00"),
        status=CourseStatus.PUBLISHED,
        instructor_id=instructor.id,
        created_by=admin.id,
    )
    db.add(course)
    db.flush()

    batch = Batch(
        course_id=course.id,
        instructor_id=instructor.id,
        name="Cohort 1",
        code="C1-2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 1),
        max_students=30,
        status=BatchStatus.ACTIVE,
    )
    db.add(batch)
    db.flush()

    enr = Enrollment(student_id=stu.id, course_id=course.id, batch_id=batch.id, status=EnrollmentStatus.ACTIVE)
    bs = BatchStudent(batch_id=batch.id, student_id=stu.id, is_active=True)
    db.add_all([enr, bs])
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    limiter.enabled = False
    client = TestClient(app)

    # Login tokens
    r_admin = client.post("/api/auth/login", json={"email": "admin@test.edu", "password": "Password@123"})
    admin_token = r_admin.json()["access_token"]

    r_stu = client.post("/api/auth/login", json={"email": "alice@test.edu", "password": "Password@123"})
    stu_token = r_stu.json()["access_token"]

    yield {
        "client": client,
        "db": db,
        "admin": admin,
        "stu": stu,
        "course": course,
        "batch": batch,
        "admin_token": admin_token,
        "stu_token": stu_token,
    }

    app.dependency_overrides.clear()
    limiter.enabled = True


def test_partial_payments_leading_to_paid_and_receipt(pay_ctx):
    client = pay_ctx["client"]
    admin_hdr = {"Authorization": f"Bearer {pay_ctx['admin_token']}"}
    stu_hdr = {"Authorization": f"Bearer {pay_ctx['stu_token']}"}
    stu_id = pay_ctx["stu"].id
    course_id = pay_ctx["course"].id

    # 1. First partial payment: $400 out of $1000
    res1 = client.post(
        "/api/payments",
        json={
            "student_id": stu_id,
            "course_id": course_id,
            "amount": 400.0,
            "payment_method": "Bank Transfer",
            "notes": "First installment",
        },
        headers=admin_hdr,
    )
    assert res1.status_code == 201, res1.text
    p1 = res1.json()
    assert p1["status"] == "Partially Paid"
    assert p1["amount_paid"] == 400.0
    assert p1["receipt_number"].startswith("RCP-")

    # Student views own payments
    res_me1 = client.get("/api/payments/me", headers=stu_hdr)
    assert res_me1.status_code == 200
    me_data1 = res_me1.json()
    assert len(me_data1["payments"]) == 1
    assert me_data1["fee_summaries"][0]["total_paid"] == 400.0
    assert me_data1["fee_summaries"][0]["total_pending"] == 600.0
    assert me_data1["fee_summaries"][0]["status"] == "Partially Paid"

    # Download receipt for p1
    res_rcp1 = client.get(f"/api/payments/{p1['id']}/receipt", headers=stu_hdr)
    assert res_rcp1.status_code == 200
    assert res_rcp1.headers["content-type"] == "application/pdf"
    assert res_rcp1.content.startswith(b"%PDF-")

    # 2. Second payment: $600 completing the fee
    res2 = client.post(
        "/api/payments",
        json={
            "student_id": stu_id,
            "course_id": course_id,
            "amount": 600.0,
            "payment_method": "UPI",
            "notes": "Final installment",
        },
        headers=admin_hdr,
    )
    assert res2.status_code == 201
    p2 = res2.json()
    assert p2["status"] == "Paid"

    # Check student balance now fully Paid
    res_me2 = client.get("/api/payments/me", headers=stu_hdr)
    assert res_me2.status_code == 200
    me_data2 = res_me2.json()
    assert len(me_data2["payments"]) == 2
    assert me_data2["fee_summaries"][0]["total_paid"] == 1000.0
    assert me_data2["fee_summaries"][0]["total_pending"] == 0.0
    assert me_data2["fee_summaries"][0]["status"] == "Paid"


def test_overpayment_rejected(pay_ctx):
    client = pay_ctx["client"]
    admin_hdr = {"Authorization": f"Bearer {pay_ctx['admin_token']}"}
    stu_id = pay_ctx["stu"].id
    course_id = pay_ctx["course"].id

    # Pay $800 of $1000
    client.post(
        "/api/payments",
        json={"student_id": stu_id, "course_id": course_id, "amount": 800.0},
        headers=admin_hdr,
    )

    # Attempt to pay $250 (remaining is only $200) -> must be rejected
    res_over = client.post(
        "/api/payments",
        json={"student_id": stu_id, "course_id": course_id, "amount": 250.0},
        headers=admin_hdr,
    )
    assert res_over.status_code in (400, 409)
    assert "exceeds" in res_over.json()["detail"].lower()


def test_status_consistency_after_refund(pay_ctx):
    client = pay_ctx["client"]
    admin_hdr = {"Authorization": f"Bearer {pay_ctx['admin_token']}"}
    stu_hdr = {"Authorization": f"Bearer {pay_ctx['stu_token']}"}
    stu_id = pay_ctx["stu"].id
    course_id = pay_ctx["course"].id

    # Pay full fee $1000
    res_pay = client.post(
        "/api/payments",
        json={"student_id": stu_id, "course_id": course_id, "amount": 1000.0},
        headers=admin_hdr,
    )
    p_id = res_pay.json()["id"]

    # Refund the payment
    res_ref = client.post(
        f"/api/payments/{p_id}/refund",
        json={"reason": "Student requested course drop within refund window"},
        headers=admin_hdr,
    )
    assert res_ref.status_code == 200
    assert res_ref.json()["status"] == "Refunded"

    # Check student balance reflects refund
    res_me = client.get("/api/payments/me", headers=stu_hdr)
    me_data = res_me.json()
    assert me_data["fee_summaries"][0]["total_paid"] == 0.0
    assert me_data["fee_summaries"][0]["total_pending"] == 1000.0
    assert me_data["fee_summaries"][0]["status"] == "Refunded"

    # Second refund attempt rejected
    res_ref_again = client.post(
        f"/api/payments/{p_id}/refund",
        json={"reason": "Duplicate attempt"},
        headers=admin_hdr,
    )
    assert res_ref_again.status_code == 400


def test_student_cannot_create_payment(pay_ctx):
    client = pay_ctx["client"]
    stu_hdr = {"Authorization": f"Bearer {pay_ctx['stu_token']}"}
    stu_id = pay_ctx["stu"].id
    course_id = pay_ctx["course"].id

    res = client.post(
        "/api/payments",
        json={"student_id": stu_id, "course_id": course_id, "amount": 100.0},
        headers=stu_hdr,
    )
    assert res.status_code == 403


def test_certificate_blocked_when_ineligible_and_generated_when_eligible(pay_ctx):
    client = pay_ctx["client"]
    stu_hdr = {"Authorization": f"Bearer {pay_ctx['stu_token']}"}
    admin_hdr = {"Authorization": f"Bearer {pay_ctx['admin_token']}"}
    db = pay_ctx["db"]
    stu = pay_ctx["stu"]
    course = pay_ctx["course"]
    batch = pay_ctx["batch"]

    # 1. Before meeting rules, generation is blocked (400)
    res_blocked = client.post(
        "/api/certificates/generate",
        json={"course_id": course.id},
        headers=stu_hdr,
    )
    assert res_blocked.status_code == 400
    assert "not eligible" in res_blocked.json()["detail"].lower()

    # 2. Setup eligible academic record:
    # A) 1 lecture completed
    mod = CourseModule(course_id=course.id, title="Module 1", sort_order=1)
    db.add(mod)
    db.flush()

    lec = Lecture(module_id=mod.id, title="Lecture 1", sort_order=1, created_by=pay_ctx["admin"].id)
    db.add(lec)
    db.flush()

    lp = LectureProgress(student_id=stu.id, lecture_id=lec.id, is_completed=True, completed_at=datetime.now(timezone.utc))
    db.add(lp)

    # B) 1 assignment submitted
    assign = Assignment(
        course_id=course.id,
        batch_id=batch.id,
        title="Project 1",
        description="Complete project",
        max_marks=100.0,
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        created_by=pay_ctx["admin"].id,
    )
    db.add(assign)
    db.flush()

    sub = Submission(
        assignment_id=assign.id,
        student_id=stu.id,
        status=SubmissionStatus.SUBMITTED,
        file_name="proj.zip",
        file_url="proj.zip",
        file_size_bytes=1024,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(sub)

    # C) 1 quiz attempted
    quiz = Quiz(
        title="Quiz 1",
        course_id=course.id,
        batch_id=batch.id,
        total_marks=Decimal("10.00"),
        passing_marks=Decimal("5.00"),
        time_limit_minutes=30,
        is_published=True,
        created_by=pay_ctx["admin"].id,
    )
    db.add(quiz)
    db.flush()

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=stu.id,
        attempt_number=1,
        started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        submitted_at=datetime.now(timezone.utc),
        score=Decimal("9.00"),
        is_passed=True,
    )
    db.add(attempt)

    # D) 1 class session with Present attendance
    session = ClassSession(batch_id=batch.id, class_date=date(2026, 2, 1), status=ClassSessionStatus.HELD, updated_by=pay_ctx["admin"].id)
    att = Attendance(batch_id=batch.id, student_id=stu.id, class_date=date(2026, 2, 1), status=AttendanceStatus.PRESENT, marked_by=pay_ctx["admin"].id)
    db.add_all([session, att])
    db.commit()

    # 3. Now generate certificate as student
    res_gen = client.post(
        "/api/certificates/generate",
        json={"course_id": course.id},
        headers=stu_hdr,
    )
    assert res_gen.status_code == 201, res_gen.text
    cert_data = res_gen.json()
    assert cert_data["certificate_number"].startswith("LMS-")
    assert cert_data["verification_code"].startswith("VER-")
    cert_id = cert_data["id"]
    ver_code = cert_data["verification_code"]

    # 4. Duplicate generation must be blocked (409)
    res_dup = client.post(
        "/api/certificates/generate",
        json={"course_id": course.id},
        headers=stu_hdr,
    )
    assert res_dup.status_code == 409
    assert "already generated" in res_dup.json()["detail"].lower()

    # 5. Download certificate PDF
    res_down = client.get(f"/api/certificates/{cert_id}/download", headers=stu_hdr)
    assert res_down.status_code == 200
    assert res_down.headers["content-type"] == "application/pdf"
    assert res_down.content.startswith(b"%PDF-")

    # 6. Public verification lookup
    res_ver = client.get(f"/api/certificates/verify/{ver_code}")
    assert res_ver.status_code == 200
    v_data = res_ver.json()
    assert v_data["valid"] is True
    assert v_data["student_name"] == stu.full_name
    assert v_data["course_title"] == course.title

    # Verification with invalid code
    res_inv = client.get("/api/certificates/verify/INVALID-CODE-999")
    assert res_inv.status_code == 200
    assert res_inv.json()["valid"] is False
