from datetime import date, datetime, timezone
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
    Base,
    Batch,
    BatchStatus,
    BatchStudent,
    Certificate,
    Course,
    CourseStatus,
    Enrollment,
    EnrollmentStatus,
    Instructor,
    Payment,
    PaymentStatus,
    Role,
    User,
)
from app.utils.limiter import limiter  # noqa: E402
from app.utils.security import hash_password  # noqa: E402


@pytest.fixture()
def sec_ctx():
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
    admin = User(role_id=admin_role.id, full_name="Admin User", email="admin@sec.edu", password_hash=pw, is_active=True)
    inst_u = User(role_id=inst_role.id, full_name="Inst User", email="inst@sec.edu", password_hash=pw, is_active=True)
    stu_a = User(role_id=stu_role.id, full_name="Student A", email="stua@sec.edu", password_hash=pw, is_active=True)
    stu_b = User(role_id=stu_role.id, full_name="Student B", email="stub@sec.edu", password_hash=pw, is_active=True)
    db.add_all([admin, inst_u, stu_a, stu_b])
    db.flush()

    instructor = Instructor(user_id=inst_u.id, expertise="Security")
    db.add(instructor)
    db.flush()

    course = Course(
        title="AppSec 101",
        code="SEC-101",
        description="Security Course",
        fee_amount=Decimal("500.00"),
        status=CourseStatus.PUBLISHED,
        instructor_id=instructor.id,
        created_by=admin.id,
    )
    db.add(course)
    db.flush()

    batch = Batch(
        course_id=course.id,
        instructor_id=instructor.id,
        name="Sec Cohort",
        code="SEC-B1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 1),
        max_students=30,
        status=BatchStatus.ACTIVE,
    )
    db.add(batch)
    db.flush()

    enr_a = Enrollment(student_id=stu_a.id, course_id=course.id, batch_id=batch.id, status=EnrollmentStatus.ACTIVE)
    enr_b = Enrollment(student_id=stu_b.id, course_id=course.id, batch_id=batch.id, status=EnrollmentStatus.ACTIVE)
    bs_a = BatchStudent(batch_id=batch.id, student_id=stu_a.id, is_active=True)
    bs_b = BatchStudent(batch_id=batch.id, student_id=stu_b.id, is_active=True)
    db.add_all([enr_a, enr_b, bs_a, bs_b])
    db.flush()

    pay_b = Payment(
        student_id=stu_b.id,
        course_id=course.id,
        enrollment_id=enr_b.id,
        amount_due=Decimal("500.00"),
        amount_paid=Decimal("500.00"),
        payment_method="UPI",
        transaction_ref="TXN-B",
        receipt_number="RCP-2026-BBBB1111",
        status=PaymentStatus.PAID,
        paid_at=datetime.now(timezone.utc),
        recorded_by=admin.id,
    )
    cert_b = Certificate(
        student_id=stu_b.id,
        course_id=course.id,
        batch_id=batch.id,
        certificate_number="LMS-2026-BBBB1111",
        verification_code="VER-BBBB11112222",
        issued_at=datetime.now(timezone.utc),
        file_name="cert_b.pdf",
        file_url="certificates/cert_b.pdf",
        issued_by=admin.id,
    )
    db.add_all([pay_b, cert_b])
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    limiter.enabled = False
    client = TestClient(app)

    admin_token = client.post("/api/auth/login", json={"email": "admin@sec.edu", "password": "Password@123"}).json()["access_token"]
    stu_a_token = client.post("/api/auth/login", json={"email": "stua@sec.edu", "password": "Password@123"}).json()["access_token"]

    yield {
        "client": client,
        "admin": admin,
        "stu_a": stu_a,
        "stu_b": stu_b,
        "pay_b": pay_b,
        "cert_b": cert_b,
        "admin_token": admin_token,
        "stu_a_token": stu_a_token,
    }

    app.dependency_overrides.clear()
    limiter.enabled = True


def test_unauthenticated_endpoints_return_401(sec_ctx):
    client = sec_ctx["client"]
    protected_gets = [
        "/api/auth/me",
        "/api/users",
        "/api/courses",
        "/api/batches",
        "/api/students",
        "/api/assignments",
        "/api/quizzes",
        "/api/attendance/me",
        "/api/progress/me",
        "/api/payments/me",
        "/api/certificates/me",
    ]
    for url in protected_gets:
        res = client.get(url)
        assert res.status_code == 401, f"Expected 401 for {url}, got {res.status_code}"


def test_idor_student_cannot_access_other_student_records(sec_ctx):
    client = sec_ctx["client"]
    hdr_a = {"Authorization": f"Bearer {sec_ctx['stu_a_token']}"}
    stu_b_id = sec_ctx["stu_b"].id
    pay_b_id = sec_ctx["pay_b"].id
    cert_b_id = sec_ctx["cert_b"].id

    assert client.get(f"/api/students/{stu_b_id}", headers=hdr_a).status_code == 403
    assert client.get(f"/api/progress/student/{stu_b_id}", headers=hdr_a).status_code == 403
    assert client.get(f"/api/payments/{pay_b_id}/receipt", headers=hdr_a).status_code == 403
    assert client.get(f"/api/certificates/{cert_b_id}/download", headers=hdr_a).status_code == 403


def test_mass_assignment_and_no_password_hash_leak(sec_ctx):
    client = sec_ctx["client"]
    hdr_a = {"Authorization": f"Bearer {sec_ctx['stu_a_token']}"}
    hdr_admin = {"Authorization": f"Bearer {sec_ctx['admin_token']}"}

    # Attempt privilege escalation via PUT /api/auth/me
    res_me = client.put(
        "/api/auth/me",
        json={"full_name": "Student A Updated", "role_id": 1, "role_name": "Admin", "is_active": False},
        headers=hdr_a,
    )
    assert res_me.status_code == 200
    body_me = res_me.json()
    assert body_me["role_name"] == "Student"
    assert "password_hash" not in body_me

    # Verify /api/users list does not expose password_hash
    res_users = client.get("/api/users", headers=hdr_admin)
    assert res_users.status_code == 200
    for item in res_users.json()["items"]:
        assert "password_hash" not in item


def test_validation_pagination_and_sqli_safety(sec_ctx):
    client = sec_ctx["client"]
    hdr_admin = {"Authorization": f"Bearer {sec_ctx['admin_token']}"}

    # Invalid pagination parameters -> 422
    assert client.get("/api/users?page=0", headers=hdr_admin).status_code == 422
    assert client.get("/api/courses?page_size=500", headers=hdr_admin).status_code == 422

    # SQL injection attempt in search query safely returns 200 with empty items
    res_sqli = client.get("/api/users?q=' OR '1'='1'; DROP TABLE users; --", headers=hdr_admin)
    assert res_sqli.status_code == 200
    assert res_sqli.json()["items"] == []
