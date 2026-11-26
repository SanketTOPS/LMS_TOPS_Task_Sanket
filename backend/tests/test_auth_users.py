from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from jose import jwt
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
from app.models import Base, Role, User  # noqa: E402
from app.utils.limiter import limiter  # noqa: E402
from app.utils.security import hash_password  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Seed roles + users
    admin_role = Role(name="Admin", description="Admin")
    instructor_role = Role(name="Instructor", description="Instructor")
    student_role = Role(name="Student", description="Student")
    db.add_all([admin_role, instructor_role, student_role])
    db.flush()

    pw_hash = hash_password("Password@123")
    admin = User(
        role_id=admin_role.id,
        full_name="Test Admin",
        email="admin@test.edu",
        password_hash=pw_hash,
        is_active=True,
    )
    student = User(
        role_id=student_role.id,
        full_name="Test Student",
        email="student@test.edu",
        password_hash=pw_hash,
        is_active=True,
    )
    inactive_user = User(
        role_id=student_role.id,
        full_name="Inactive Student",
        email="inactive@test.edu",
        password_hash=pw_hash,
        is_active=False,
    )
    db.add_all([admin, student, inactive_user])
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    # Reset rate limiter storage between tests
    limiter.reset()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _auth_header(client: TestClient, email: str, password: str = "Password@123") -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_valid_login_returns_jwt_without_password_hash(client: TestClient) -> None:
    resp = client.post(
        "/api/auth/login",
        json={"email": "admin@test.edu", "password": "Password@123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@test.edu"
    assert data["user"]["role_name"] == "Admin"
    assert "password_hash" not in data["user"]


def test_invalid_login_uses_one_generic_error_message(client: TestClient) -> None:
    wrong_email = client.post(
        "/api/auth/login",
        json={"email": "nobody@test.edu", "password": "Password@123"},
    )
    wrong_pw = client.post(
        "/api/auth/login",
        json={"email": "admin@test.edu", "password": "WrongPassword1"},
    )
    assert wrong_email.status_code == 401
    assert wrong_pw.status_code == 401
    assert wrong_email.json()["detail"] == wrong_pw.json()["detail"]
    assert wrong_email.json()["code"] == "INVALID_CREDENTIALS"


def test_inactive_user_cannot_login(client: TestClient) -> None:
    resp = client.post(
        "/api/auth/login",
        json={"email": "inactive@test.edu", "password": "Password@123"},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "INACTIVE_USER"


def test_expired_token_rejected(client: TestClient) -> None:
    expired_payload = {
        "sub": "1",
        "role": "Admin",
        "type": "access",
        "exp": int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp()),
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_TOKEN"


def test_student_cannot_call_admin_endpoints(client: TestClient) -> None:
    headers = _auth_header(client, "student@test.edu")

    assert client.get("/api/users", headers=headers).status_code == 403
    assert (
        client.post(
            "/api/users",
            headers=headers,
            json={
                "full_name": "New User",
                "email": "new@test.edu",
                "password": "Password@123",
                "role_name": "Student",
            },
        ).status_code
        == 403
    )
    assert client.put("/api/users/1", headers=headers, json={"full_name": "X"}).status_code == 403
    assert client.patch("/api/users/1/deactivate", headers=headers).status_code == 403
    assert (
        client.post(
            "/api/users/1/reset-password",
            headers=headers,
            json={"new_password": "Password@456"},
        ).status_code
        == 403
    )


def test_admin_create_user_duplicate_email_returns_409(client: TestClient) -> None:
    headers = _auth_header(client, "admin@test.edu")

    resp = client.post(
        "/api/users",
        headers=headers,
        json={
            "full_name": "Duplicate Student",
            "email": "student@test.edu",
            "password": "Password@123",
            "role_name": "Student",
        },
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "EMAIL_ALREADY_EXISTS"


def test_profile_and_change_password(client: TestClient) -> None:
    headers = _auth_header(client, "student@test.edu")

    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "student@test.edu"

    upd_resp = client.put(
        "/api/auth/me",
        headers=headers,
        json={"full_name": "Updated Student", "phone": "+91-9999999999"},
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["full_name"] == "Updated Student"

    chg_resp = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"current_password": "Password@123", "new_password": "NewPassword@456"},
    )
    assert chg_resp.status_code == 200

    # Login with new password works
    new_login = client.post(
        "/api/auth/login",
        json={"email": "student@test.edu", "password": "NewPassword@456"},
    )
    assert new_login.status_code == 200


def test_admin_user_lifecycle(client: TestClient) -> None:
    headers = _auth_header(client, "admin@test.edu")

    # Create Instructor
    create_resp = client.post(
        "/api/users",
        headers=headers,
        json={
            "full_name": "Instructor One",
            "email": "inst1@test.edu",
            "password": "Password@123",
            "role_name": "Instructor",
        },
    )
    assert create_resp.status_code == 201
    created_id = create_resp.json()["id"]

    # List with filter
    list_resp = client.get("/api/users?role=Instructor&q=inst1", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    # Deactivate
    deact_resp = client.patch(f"/api/users/{created_id}/deactivate", headers=headers)
    assert deact_resp.status_code == 200
    assert deact_resp.json()["is_active"] is False
