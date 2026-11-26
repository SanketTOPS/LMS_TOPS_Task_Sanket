from datetime import date
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
from app.models import Base, Instructor, Role, User  # noqa: E402
from app.utils.limiter import limiter  # noqa: E402
from app.utils.security import hash_password  # noqa: E402


@pytest.fixture()
def seeded_ctx():
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
    admin = User(role_id=admin_role.id, full_name="Admin", email="admin@t.edu", password_hash=pw, is_active=True)
    inst1_u = User(role_id=inst_role.id, full_name="Inst One", email="inst1@t.edu", password_hash=pw, is_active=True)
    inst2_u = User(role_id=inst_role.id, full_name="Inst Two", email="inst2@t.edu", password_hash=pw, is_active=True)
    stu1 = User(role_id=stu_role.id, full_name="Student One", email="stu1@t.edu", password_hash=pw, is_active=True)
    stu2 = User(role_id=stu_role.id, full_name="Student Two", email="stu2@t.edu", password_hash=pw, is_active=True)
    db.add_all([admin, inst1_u, inst2_u, stu1, stu2])
    db.flush()

    inst1 = Instructor(user_id=inst1_u.id, expertise="FastAPI", is_active=True)
    inst2 = Instructor(user_id=inst2_u.id, expertise="React", is_active=True)
    db.add_all([inst1, inst2])
    db.commit()

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    limiter.reset()

    with TestClient(app) as client:
        yield {
            "client": client,
            "inst1_id": inst1.id,
            "inst2_id": inst2.id,
            "stu1_id": stu1.id,
            "stu2_id": stu2.id,
        }

    app.dependency_overrides.clear()
    db.close()
    Base.metadata.drop_all(bind=engine)


def _login(client: TestClient, email: str) -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"email": email, "password": "Password@123"})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_batch_date_validation(seeded_ctx) -> None:
    client = seeded_ctx["client"]
    admin_h = _login(client, "admin@t.edu")

    course = client.post(
        "/api/courses",
        headers=admin_h,
        json={"title": "Python", "code": "PY-101", "instructor_id": seeded_ctx["inst1_id"]},
    ).json()

    resp = client.post(
        "/api/batches",
        headers=admin_h,
        json={
            "course_id": course["id"],
            "instructor_id": seeded_ctx["inst1_id"],
            "name": "Bad Dates Batch",
            "code": "BAD-01",
            "start_date": str(date(2026, 12, 10)),
            "end_date": str(date(2026, 12, 5)),
            "max_students": 10,
        },
    )
    assert resp.status_code == 422


def test_capacity_limit_and_duplicate_enrollment(seeded_ctx) -> None:
    client = seeded_ctx["client"]
    admin_h = _login(client, "admin@t.edu")

    course = client.post(
        "/api/courses",
        headers=admin_h,
        json={"title": "Web Dev", "code": "WEB-101", "instructor_id": seeded_ctx["inst1_id"]},
    ).json()
    batch = client.post(
        "/api/batches",
        headers=admin_h,
        json={
            "course_id": course["id"],
            "instructor_id": seeded_ctx["inst1_id"],
            "name": "Small Batch",
            "code": "WEB-B1",
            "start_date": "2026-12-01",
            "end_date": "2027-01-01",
            "max_students": 1,
        },
    ).json()

    # Add first student -> 201
    r1 = client.post(
        f"/api/batches/{batch['id']}/students",
        headers=admin_h,
        json={"student_id": seeded_ctx["stu1_id"]},
    )
    assert r1.status_code == 201

    # Duplicate enrollment -> 409
    r_dup = client.post(
        f"/api/batches/{batch['id']}/students",
        headers=admin_h,
        json={"student_id": seeded_ctx["stu1_id"]},
    )
    assert r_dup.status_code == 409
    assert r_dup.json()["code"] == "DUPLICATE_ENROLLMENT"

    # Capacity full -> 409
    r_full = client.post(
        f"/api/batches/{batch['id']}/students",
        headers=admin_h,
        json={"student_id": seeded_ctx["stu2_id"]},
    )
    assert r_full.status_code == 409
    assert r_full.json()["code"] == "BATCH_CAPACITY_FULL"

    # Deleting course with active batch/enrollments -> 409
    r_del = client.delete(f"/api/courses/{course['id']}", headers=admin_h)
    assert r_del.status_code == 409
    assert r_del.json()["code"] == "COURSE_IN_USE"

    # Student detail includes enrollment + batch + stubs
    stu_detail = client.get(f"/api/students/{seeded_ctx['stu1_id']}", headers=admin_h)
    assert stu_detail.status_code == 200
    assert len(stu_detail.json()["enrollments"]) == 1
    assert stu_detail.json()["attendance_percentage"] == 0.0


def test_instructor_cannot_edit_unassigned_course(seeded_ctx) -> None:
    client = seeded_ctx["client"]
    admin_h = _login(client, "admin@t.edu")
    inst2_h = _login(client, "inst2@t.edu")

    course = client.post(
        "/api/courses",
        headers=admin_h,
        json={"title": "Course For Inst1", "code": "C-101", "instructor_id": seeded_ctx["inst1_id"]},
    ).json()

    resp = client.put(
        f"/api/courses/{course['id']}",
        headers=inst2_h,
        json={"description": "Unauthorized edit"},
    )
    assert resp.status_code == 403


def test_student_cannot_list_other_batches(seeded_ctx) -> None:
    client = seeded_ctx["client"]
    admin_h = _login(client, "admin@t.edu")
    stu1_h = _login(client, "stu1@t.edu")

    course = client.post(
        "/api/courses",
        headers=admin_h,
        json={"title": "Course X", "code": "CX-1", "instructor_id": seeded_ctx["inst1_id"], "status": "published"},
    ).json()
    b1 = client.post(
        "/api/batches",
        headers=admin_h,
        json={
            "course_id": course["id"],
            "instructor_id": seeded_ctx["inst1_id"],
            "name": "Batch 1",
            "code": "B-1",
            "start_date": "2026-12-01",
            "end_date": "2027-01-01",
        },
    ).json()
    b2 = client.post(
        "/api/batches",
        headers=admin_h,
        json={
            "course_id": course["id"],
            "instructor_id": seeded_ctx["inst1_id"],
            "name": "Batch 2",
            "code": "B-2",
            "start_date": "2026-12-01",
            "end_date": "2027-01-01",
        },
    ).json()

    # Enroll stu1 only in b1
    client.post(f"/api/batches/{b1['id']}/students", headers=admin_h, json={"student_id": seeded_ctx["stu1_id"]})

    list_resp = client.get("/api/batches", headers=stu1_h)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1
    assert list_resp.json()["items"][0]["id"] == b1["id"]

    # Accessing b2 directly is 403
    other_resp = client.get(f"/api/batches/{b2['id']}", headers=stu1_h)
    assert other_resp.status_code == 403
