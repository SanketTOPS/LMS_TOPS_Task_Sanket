from datetime import datetime, timedelta, timezone
import io
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

from app.config import settings  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, Course, CourseStatus, Enrollment, Instructor, Role, User  # noqa: E402
from app.utils.limiter import limiter  # noqa: E402
from app.utils.security import hash_password  # noqa: E402


@pytest.fixture()
def assign_ctx(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 2)

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
    admin = User(role_id=admin_role.id, full_name="Admin", email="admin@a.edu", password_hash=pw, is_active=True)
    inst_u = User(role_id=inst_role.id, full_name="Inst", email="inst@a.edu", password_hash=pw, is_active=True)
    stu1 = User(role_id=stu_role.id, full_name="Stu1", email="stu1@a.edu", password_hash=pw, is_active=True)
    stu2 = User(role_id=stu_role.id, full_name="Stu2", email="stu2@a.edu", password_hash=pw, is_active=True)
    db.add_all([admin, inst_u, stu1, stu2])
    db.flush()

    inst = Instructor(user_id=inst_u.id, is_active=True)
    db.add(inst)
    db.flush()

    course = Course(
        title="Backend Eng",
        code="BE-101",
        status=CourseStatus.PUBLISHED,
        instructor_id=inst.id,
        created_by=admin.id,
    )
    db.add(course)
    db.flush()

    db.add_all([
        Enrollment(student_id=stu1.id, course_id=course.id),
        Enrollment(student_id=stu2.id, course_id=course.id),
    ])
    db.commit()

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    limiter.reset()

    with TestClient(app) as client:
        yield {"client": client, "course_id": course.id}

    app.dependency_overrides.clear()
    db.close()
    Base.metadata.drop_all(bind=engine)


def _login(client: TestClient, email: str) -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"email": email, "password": "Password@123"})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_late_submission_flag_and_version_history(assign_ctx) -> None:
    client = assign_ctx["client"]
    inst_h = _login(client, "inst@a.edu")
    stu1_h = _login(client, "stu1@a.edu")

    past_due = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    a_resp = client.post(
        "/api/assignments",
        headers=inst_h,
        json={
            "course_id": assign_ctx["course_id"],
            "title": "Late Allowed Task",
            "max_marks": 50,
            "due_date": past_due,
            "allow_late": True,
        },
    )
    assert a_resp.status_code == 201
    a_id = a_resp.json()["id"]

    pdf = b"%PDF-1.4\n%submission\n"
    s1 = client.post(
        "/api/submissions",
        headers=stu1_h,
        data={"assignment_id": str(a_id), "submission_text": "Attempt 1"},
        files={"file": ("hw1.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert s1.status_code == 201
    assert s1.json()["status"] == "Late Submission"
    assert len(s1.json()["versions"]) == 1

    # Resubmission increments version history
    s2 = client.post(
        "/api/submissions",
        headers=stu1_h,
        data={"assignment_id": str(a_id), "submission_text": "Attempt 2"},
        files={"file": ("hw2.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert s2.status_code == 201
    assert len(s2.json()["versions"]) == 2


def test_marks_exceed_max_and_student_isolation(assign_ctx) -> None:
    client = assign_ctx["client"]
    inst_h = _login(client, "inst@a.edu")
    stu1_h = _login(client, "stu1@a.edu")
    stu2_h = _login(client, "stu2@a.edu")

    future_due = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    a_resp = client.post(
        "/api/assignments",
        headers=inst_h,
        json={
            "course_id": assign_ctx["course_id"],
            "title": "API Spec",
            "max_marks": 100,
            "due_date": future_due,
            "allow_late": False,
        },
    )
    assert a_resp.status_code == 201
    a_id = a_resp.json()["id"]

    pdf = b"%PDF-1.4\n%stu1\n"
    sub = client.post(
        "/api/submissions",
        headers=stu1_h,
        data={"assignment_id": str(a_id), "submission_text": "My work"},
        files={"file": ("work.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert sub.status_code == 201
    sub_id = sub.json()["id"]
    assert sub.json()["status"] == "Submitted"

    # Student cannot list all submissions or download stu1's submission
    assert client.get(f"/api/assignments/{a_id}/submissions", headers=stu2_h).status_code == 403
    assert client.get(f"/api/submissions/{sub_id}/download", headers=stu2_h).status_code == 403

    # Student cannot edit marks
    assert (
        client.post(
            f"/api/submissions/{sub_id}/evaluate",
            headers=stu1_h,
            json={"marks": 100, "comments": "Self grade"},
        ).status_code
        == 403
    )

    # Marks > max_marks rejected (422)
    bad_grade = client.post(
        f"/api/submissions/{sub_id}/evaluate",
        headers=inst_h,
        json={"marks": 120, "comments": "Too high"},
    )
    assert bad_grade.status_code == 422
    assert bad_grade.json()["code"] == "MARKS_EXCEED_MAX"

    # Valid evaluation succeeds
    ok_grade = client.post(
        f"/api/submissions/{sub_id}/evaluate",
        headers=inst_h,
        json={"marks": 92, "comments": "Great job"},
    )
    assert ok_grade.status_code == 200
    assert ok_grade.json()["status"] == "Evaluated"

    # Deleting assignment with submissions -> 409
    assert client.delete(f"/api/assignments/{a_id}", headers=inst_h).status_code == 409
