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
from app.models import Base, Course, CourseModule, CourseStatus, Enrollment, Instructor, Role, User  # noqa: E402
from app.utils.limiter import limiter  # noqa: E402
from app.utils.security import hash_password  # noqa: E402


@pytest.fixture()
def lecture_ctx(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)

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
    admin = User(role_id=admin_role.id, full_name="Admin", email="admin@l.edu", password_hash=pw, is_active=True)
    inst_u = User(role_id=inst_role.id, full_name="Inst", email="inst@l.edu", password_hash=pw, is_active=True)
    enrolled_stu = User(role_id=stu_role.id, full_name="Enrolled", email="enr@l.edu", password_hash=pw, is_active=True)
    unenrolled_stu = User(role_id=stu_role.id, full_name="Unenrolled", email="unenr@l.edu", password_hash=pw, is_active=True)
    db.add_all([admin, inst_u, enrolled_stu, unenrolled_stu])
    db.flush()

    inst = Instructor(user_id=inst_u.id, is_active=True)
    db.add(inst)
    db.flush()

    course = Course(
        title="FastAPI Mastery",
        code="FA-101",
        status=CourseStatus.PUBLISHED,
        instructor_id=inst.id,
        created_by=admin.id,
    )
    db.add(course)
    db.flush()

    mod = CourseModule(course_id=course.id, title="Module 1", sort_order=1)
    db.add(mod)
    db.flush()

    enr = Enrollment(student_id=enrolled_stu.id, course_id=course.id)
    db.add(enr)
    db.commit()

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    limiter.reset()

    with TestClient(app) as client:
        yield {
            "client": client,
            "course_id": course.id,
            "module_id": mod.id,
        }

    app.dependency_overrides.clear()
    db.close()
    Base.metadata.drop_all(bind=engine)


def _login(client: TestClient, email: str) -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"email": email, "password": "Password@123"})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_unenrolled_student_blocked_and_completion_idempotent(lecture_ctx) -> None:
    client = lecture_ctx["client"]
    inst_h = _login(client, "inst@l.edu")
    enr_h = _login(client, "enr@l.edu")
    unenr_h = _login(client, "unenr@l.edu")

    # Instructor creates a lecture
    lec = client.post(
        "/api/lectures",
        headers=inst_h,
        json={
            "module_id": lecture_ctx["module_id"],
            "title": "Intro Lecture",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "duration_minutes": 20,
            "sort_order": 1,
        },
    )
    assert lec.status_code == 201
    lec_id = lec.json()["id"]

    # Instructor uploads valid PDF material
    pdf_bytes = b"%PDF-1.4\n%Valid test PDF content\n"
    mat = client.post(
        "/api/materials",
        headers=inst_h,
        data={
            "course_id": str(lecture_ctx["course_id"]),
            "module_id": str(lecture_ctx["module_id"]),
            "lecture_id": str(lec_id),
            "title": "Slides PDF",
        },
        files={"file": ("slides.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert mat.status_code == 201
    mat_id = mat.json()["id"]

    # Unenrolled student blocked everywhere -> 403
    assert client.get(f"/api/courses/{lecture_ctx['course_id']}/lectures", headers=unenr_h).status_code == 403
    assert client.get(f"/api/lectures/{lec_id}", headers=unenr_h).status_code == 403
    assert client.post(f"/api/lectures/{lec_id}/complete", headers=unenr_h).status_code == 403
    assert client.get(f"/api/materials/{mat_id}/download", headers=unenr_h).status_code == 403

    # Enrolled student can access and download
    assert client.get(f"/api/courses/{lecture_ctx['course_id']}/lectures", headers=enr_h).status_code == 200
    dl = client.get(f"/api/materials/{mat_id}/download", headers=enr_h)
    assert dl.status_code == 200
    assert dl.content == pdf_bytes

    # Completion is idempotent
    c1 = client.post(f"/api/lectures/{lec_id}/complete", headers=enr_h)
    c2 = client.post(f"/api/lectures/{lec_id}/complete", headers=enr_h)
    assert c1.status_code == 200
    assert c2.status_code == 200
    assert c2.json()["is_completed"] is True

    prog = client.get(f"/api/courses/{lecture_ctx['course_id']}/progress", headers=enr_h)
    assert prog.status_code == 200
    assert prog.json()["progress_percentage"] == 100.0


def test_invalid_file_type_and_oversized_file_rejected(lecture_ctx) -> None:
    client = lecture_ctx["client"]
    inst_h = _login(client, "inst@l.edu")

    # 1. Invalid extension (.exe)
    bad_ext = client.post(
        "/api/materials",
        headers=inst_h,
        data={"course_id": str(lecture_ctx["course_id"]), "title": "Bad"},
        files={"file": ("malware.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
    )
    assert bad_ext.status_code == 400
    assert bad_ext.json()["code"] == "INVALID_FILE_TYPE"

    # 2. Spoofed extension (.pdf with non-PDF magic bytes)
    bad_sig = client.post(
        "/api/materials",
        headers=inst_h,
        data={"course_id": str(lecture_ctx["course_id"]), "title": "Spoofed"},
        files={"file": ("fake.pdf", io.BytesIO(b"NOT_A_PDF"), "application/pdf")},
    )
    assert bad_sig.status_code == 400
    assert bad_sig.json()["code"] == "INVALID_FILE_SIGNATURE"

    # 3. Oversized file (> 1 MB limit in test fixture)
    oversized = b"%PDF-1.4\n" + (b"A" * (1024 * 1024 + 100))
    too_big = client.post(
        "/api/materials",
        headers=inst_h,
        data={"course_id": str(lecture_ctx["course_id"]), "title": "Huge PDF"},
        files={"file": ("huge.pdf", io.BytesIO(oversized), "application/pdf")},
    )
    assert too_big.status_code == 413
    assert too_big.json()["code"] == "FILE_TOO_LARGE"
