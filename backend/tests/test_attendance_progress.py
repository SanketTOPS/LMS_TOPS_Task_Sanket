from datetime import date
import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    AttendanceAudit,
    Base,
    Batch,
    BatchStatus,
    BatchStudent,
    Course,
    CourseModule,
    CourseStatus,
    Enrollment,
    Instructor,
    Lecture,
    LectureProgress,
    Role,
    User,
)
from app.utils.limiter import limiter  # noqa: E402
from app.utils.security import hash_password  # noqa: E402


@pytest.fixture()
def att_ctx():
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
    admin = User(role_id=admin_role.id, full_name="Admin", email="admin@p.edu", password_hash=pw, is_active=True)
    inst_u = User(role_id=inst_role.id, full_name="Inst", email="inst@p.edu", password_hash=pw, is_active=True)
    stu = User(role_id=stu_role.id, full_name="Student", email="stu@p.edu", password_hash=pw, is_active=True)
    db.add_all([admin, inst_u, stu])
    db.flush()

    inst = Instructor(user_id=inst_u.id, is_active=True)
    db.add(inst)
    db.flush()

    course = Course(
        title="Data Eng",
        code="DE-101",
        status=CourseStatus.PUBLISHED,
        instructor_id=inst.id,
        created_by=admin.id,
    )
    db.add(course)
    db.flush()

    mod = CourseModule(course_id=course.id, title="M1", sort_order=1)
    db.add(mod)
    db.flush()

    lec = Lecture(module_id=mod.id, title="L1", sort_order=1, is_published=True, created_by=inst_u.id)
    db.add(lec)
    db.flush()

    batch = Batch(
        course_id=course.id,
        instructor_id=inst.id,
        name="DE Batch 1",
        code="DE-B1",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 12, 31),
        status=BatchStatus.ACTIVE,
    )
    db.add(batch)
    db.flush()

    db.add(Enrollment(student_id=stu.id, course_id=course.id, batch_id=batch.id))
    db.add(BatchStudent(batch_id=batch.id, student_id=stu.id, is_active=True))
    db.add(LectureProgress(student_id=stu.id, lecture_id=lec.id, is_completed=True))
    db.commit()

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    limiter.reset()

    with TestClient(app) as client:
        yield {"client": client, "db": db, "batch_id": batch.id, "student_id": stu.id}

    app.dependency_overrides.clear()
    db.close()
    Base.metadata.drop_all(bind=engine)


def _login(client: TestClient, email: str) -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"email": email, "password": "Password@123"})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_attendance_percentage_with_cancelled_class_and_leave(att_ctx) -> None:
    client = att_ctx["client"]
    db = att_ctx["db"]
    inst_h = _login(client, "inst@p.edu")
    stu_h = _login(client, "stu@p.edu")
    b_id = att_ctx["batch_id"]
    s_id = att_ctx["student_id"]

    # Day 1: Held - Present
    assert (
        client.post(
            "/api/attendance/bulk",
            headers=inst_h,
            json={
                "batch_id": b_id,
                "class_date": "2026-11-10",
                "session_status": "held",
                "records": [{"student_id": s_id, "status": "Present"}],
            },
        ).status_code
        == 200
    )

    # Day 2: Held - Absent
    assert (
        client.post(
            "/api/attendance/bulk",
            headers=inst_h,
            json={
                "batch_id": b_id,
                "class_date": "2026-11-11",
                "session_status": "held",
                "records": [{"student_id": s_id, "status": "Absent"}],
            },
        ).status_code
        == 200
    )

    # Day 3: Cancelled class (excluded from denominator even if Absent row exists)
    assert (
        client.post(
            "/api/attendance/bulk",
            headers=inst_h,
            json={
                "batch_id": b_id,
                "class_date": "2026-11-12",
                "session_status": "cancelled",
                "records": [{"student_id": s_id, "status": "Absent"}],
            },
        ).status_code
        == 200
    )

    # Day 4: Held - Approved Leave (excluded from denominator)
    assert (
        client.post(
            "/api/attendance/bulk",
            headers=inst_h,
            json={
                "batch_id": b_id,
                "class_date": "2026-11-13",
                "session_status": "held",
                "records": [{"student_id": s_id, "status": "Approved Leave"}],
            },
        ).status_code
        == 200
    )

    # Verify audit rows were recorded
    audits = list(db.scalars(select(AttendanceAudit)).all())
    assert len(audits) == 4

    # Eligible = 2 (Nov 10 Present + Nov 11 Absent), Present = 1 -> 50.0%
    me_att = client.get("/api/attendance/me", headers=stu_h)
    assert me_att.status_code == 200
    data = me_att.json()
    assert data["total_eligible_classes"] == 2
    assert data["total_present"] == 1
    assert data["attendance_percentage"] == 50.0
    assert len(data["monthly_summary"]) == 1

    # Progress endpoint works for student
    prog = client.get("/api/progress/me", headers=stu_h)
    assert prog.status_code == 200
    assert prog.json()["courses"][0]["lectures_completed"] == 1
    assert prog.json()["courses"][0]["attendance_percentage"] == 50.0


def test_duplicate_attendance_and_student_cannot_modify(att_ctx) -> None:
    client = att_ctx["client"]
    inst_h = _login(client, "inst@p.edu")
    stu_h = _login(client, "stu@p.edu")
    b_id = att_ctx["batch_id"]
    s_id = att_ctx["student_id"]

    # Student cannot call instructor/admin attendance endpoints -> 403
    assert (
        client.post(
            "/api/attendance/bulk",
            headers=stu_h,
            json={"batch_id": b_id, "class_date": "2026-11-15", "session_status": "held", "records": []},
        ).status_code
        == 403
    )
    assert (
        client.get(f"/api/attendance/roster?batch_id={b_id}&class_date=2026-11-15", headers=stu_h).status_code
        == 403
    )
    assert client.get(f"/api/progress/student/{s_id}", headers=stu_h).status_code == 403

    # Duplicate prevention on single POST /api/attendance -> 409
    r1 = client.post(
        "/api/attendance",
        headers=inst_h,
        json={"student_id": s_id, "batch_id": b_id, "class_date": "2026-11-15", "status": "Present"},
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/attendance",
        headers=inst_h,
        json={"student_id": s_id, "batch_id": b_id, "class_date": "2026-11-15", "status": "Absent"},
    )
    assert r2.status_code == 409
    assert r2.json()["code"] == "DUPLICATE_ATTENDANCE"
