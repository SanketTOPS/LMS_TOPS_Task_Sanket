from datetime import datetime, timedelta, timezone
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
from app.models import Base, Course, CourseStatus, Enrollment, Instructor, QuizAttempt, Role, User  # noqa: E402
from app.utils.limiter import limiter  # noqa: E402
from app.utils.security import hash_password  # noqa: E402


@pytest.fixture()
def quiz_ctx():
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
    admin = User(role_id=admin_role.id, full_name="Admin", email="admin@q.edu", password_hash=pw, is_active=True)
    inst_u = User(role_id=inst_role.id, full_name="Inst", email="inst@q.edu", password_hash=pw, is_active=True)
    stu = User(role_id=stu_role.id, full_name="Student", email="stu@q.edu", password_hash=pw, is_active=True)
    db.add_all([admin, inst_u, stu])
    db.flush()

    inst = Instructor(user_id=inst_u.id, is_active=True)
    db.add(inst)
    db.flush()

    course = Course(
        title="Python Core",
        code="PY-Q1",
        status=CourseStatus.PUBLISHED,
        instructor_id=inst.id,
        created_by=admin.id,
    )
    db.add(course)
    db.flush()
    db.add(Enrollment(student_id=stu.id, course_id=course.id))
    db.commit()

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    limiter.reset()

    with TestClient(app) as client:
        yield {"client": client, "db": db, "course_id": course.id}

    app.dependency_overrides.clear()
    db.close()
    Base.metadata.drop_all(bind=engine)


def _login(client: TestClient, email: str) -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"email": email, "password": "Password@123"})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_quiz_flow_server_score_no_answer_leak_and_duplicate_blocked(quiz_ctx) -> None:
    client = quiz_ctx["client"]
    inst_h = _login(client, "inst@q.edu")
    stu_h = _login(client, "stu@q.edu")

    quiz = client.post(
        "/api/quizzes",
        headers=inst_h,
        json={
            "course_id": quiz_ctx["course_id"],
            "title": "Week 1 Quiz",
            "time_limit_minutes": 15,
            "passing_marks": 2,
            "allow_retake": False,
            "is_published": True,
        },
    ).json()
    quiz_id = quiz["id"]

    q1 = client.post(
        f"/api/quizzes/{quiz_id}/questions",
        headers=inst_h,
        json={
            "question_text": "2 + 2 = ?",
            "marks": 2,
            "sort_order": 1,
            "options": ["3", "4", "5"],
            "correct_option_index": 1,
        },
    ).json()
    q2 = client.post(
        f"/api/quizzes/{quiz_id}/questions",
        headers=inst_h,
        json={
            "question_text": "3 + 3 = ?",
            "marks": 2,
            "sort_order": 2,
            "options": ["5", "6", "7"],
            "correct_option_index": 1,
        },
    ).json()

    # Student cannot call admin/instructor question endpoint
    assert client.get(f"/api/quizzes/{quiz_id}/questions", headers=stu_h).status_code == 403

    # Start quiz -> correct_option_id must NOT be in payload
    start = client.post(f"/api/quizzes/{quiz_id}/start", headers=stu_h)
    assert start.status_code == 200
    attempt_data = start.json()
    attempt_id = attempt_data["attempt_id"]
    for q in attempt_data["questions"]:
        assert "correct_option_id" not in q

    # Answer q1 correctly, q2 wrongly
    q1_correct_opt = q1["correct_option_id"]
    q2_wrong_opt = [o["id"] for o in q2["options"] if o["id"] != q2["correct_option_id"]][0]
    assert (
        client.put(
            f"/api/quiz-attempts/{attempt_id}/answer",
            headers=stu_h,
            json={"question_id": q1["id"], "selected_option_id": q1_correct_opt},
        ).status_code
        == 200
    )
    assert (
        client.put(
            f"/api/quiz-attempts/{attempt_id}/answer",
            headers=stu_h,
            json={"question_id": q2["id"], "selected_option_id": q2_wrong_opt},
        ).status_code
        == 200
    )

    # Submit -> server computes score = 2.00 (>= passing_marks 2.00 -> is_passed=True)
    sub = client.post(f"/api/quiz-attempts/{attempt_id}/submit", headers=stu_h)
    assert sub.status_code == 200
    res = sub.json()
    assert float(res["score"]) == 2.0
    assert res["is_passed"] is True
    assert res["questions"][0]["correct_option_id"] == q1_correct_opt

    # Duplicate attempt blocked (409)
    dup = client.post(f"/api/quizzes/{quiz_id}/start", headers=stu_h)
    assert dup.status_code == 409
    assert dup.json()["code"] == "DUPLICATE_ATTEMPT"


def test_quiz_outside_window_and_timer_expiry(quiz_ctx) -> None:
    client = quiz_ctx["client"]
    db = quiz_ctx["db"]
    inst_h = _login(client, "inst@q.edu")
    stu_h = _login(client, "stu@q.edu")

    # 1. Outside window (future)
    future_quiz = client.post(
        "/api/quizzes",
        headers=inst_h,
        json={
            "course_id": quiz_ctx["course_id"],
            "title": "Future Quiz",
            "available_from": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "available_until": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "is_published": True,
        },
    ).json()
    r_win = client.post(f"/api/quizzes/{future_quiz['id']}/start", headers=stu_h)
    assert r_win.status_code == 400
    assert r_win.json()["code"] == "QUIZ_OUTSIDE_WINDOW"

    # 2. Timer expiry auto-finalisation
    timed_quiz = client.post(
        "/api/quizzes",
        headers=inst_h,
        json={
            "course_id": quiz_ctx["course_id"],
            "title": "Timed Quiz",
            "time_limit_minutes": 1,
            "passing_marks": 1,
            "is_published": True,
        },
    ).json()
    q = client.post(
        f"/api/quizzes/{timed_quiz['id']}/questions",
        headers=inst_h,
        json={
            "question_text": "1 + 1 = ?",
            "marks": 1,
            "sort_order": 1,
            "options": ["1", "2"],
            "correct_option_index": 1,
        },
    ).json()

    start = client.post(f"/api/quizzes/{timed_quiz['id']}/start", headers=stu_h).json()
    att_id = start["attempt_id"]

    # Save correct answer before expiry
    client.put(
        f"/api/quiz-attempts/{att_id}/answer",
        headers=stu_h,
        json={"question_id": q["id"], "selected_option_id": q["correct_option_id"]},
    )

    # Simulate elapsed time > time_limit_minutes + grace
    att_row = db.get(QuizAttempt, att_id)
    att_row.started_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db.commit()

    # Subsequent answer save fails with QUIZ_TIME_EXPIRED and auto-finalises
    late_ans = client.put(
        f"/api/quiz-attempts/{att_id}/answer",
        headers=stu_h,
        json={"question_id": q["id"], "selected_option_id": q["options"][0]["id"]},
    )
    assert late_ans.status_code == 400
    assert late_ans.json()["code"] == "QUIZ_TIME_EXPIRED"

    # Fetching attempt returns auto-finalised result with saved score
    fetched = client.get(f"/api/quiz-attempts/{att_id}", headers=stu_h)
    assert fetched.status_code == 200
    assert fetched.json()["is_submitted"] is True
    assert float(fetched.json()["score"]) == 1.0
