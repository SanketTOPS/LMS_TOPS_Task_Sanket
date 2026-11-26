# LMS Test Plan

## 1. Scope & Strategy

This test plan covers backend API, business logic, database constraints, and security controls across all LMS modules:
- **Auth & Users** (`test_auth_users.py`)
- **Courses & Batches** (`test_courses_batches.py`)
- **Lectures & Study Materials** (`test_lectures_materials.py`)
- **Assignments & Submissions** (`test_assignments.py`)
- **Quizzes & Attempts** (`test_quizzes.py`)
- **Attendance & Progress** (`test_attendance_progress.py`)
- **Payments & Certificates** (`test_payments_certificates.py`)
- **Security, RBAC, IDOR & Validation** (`test_security_validation.py`)
- **Health Check** (`test_health.py`)

## 2. Test Environment

- **Runner:** `pytest` 9.2.0 (`backend/venv/Scripts/pytest.exe`)
- **Database:** Isolated SQLite in-memory database per test fixture (`StaticPool`), schema initialized from SQLAlchemy `Base.metadata.create_all()`.
- **HTTP Client:** FastAPI `TestClient` with `get_db` dependency override and `limiter.enabled = False` for deterministic test execution.
- **Data:** Synthetic users (Admin, Instructor, Students), courses, batches, and enrollments created in fixtures.

## 3. Module Test Matrix

| Module | Test File | Key Scenarios Covered |
|---|---|---|
| Health | `test_health.py` | API liveness response |
| Auth & Users | `test_auth_users.py` | JWT login, generic invalid login error, inactive user block, expired token rejection, RBAC 403, duplicate email 409, password change, user lifecycle |
| Courses & Batches | `test_courses_batches.py` | Batch date validation, capacity limit & duplicate enrollment, instructor course isolation, student batch isolation |
| Lectures & Materials | `test_lectures_materials.py` | Unenrolled student access block, idempotent completion, file type & size upload validation |
| Assignments | `test_assignments.py` | Server-side late submission flag, resubmission version history, marks > max rejection, student submission isolation |
| Quizzes | `test_quizzes.py` | Server-side scoring, no correct answer leak before submit, duplicate attempt block, time window & timer expiry auto-finalisation |
| Attendance & Progress | `test_attendance_progress.py` | Cancelled/holiday/approved-leave exclusion from denominator, duplicate attendance prevention, student modification block |
| Payments & Certificates | `test_payments_certificates.py` | Partial payments -> Paid, receipt PDF generation, overpayment rejection, refund status consistency, student payment block, certificate eligibility gate, duplicate certificate 409, public verification |
| Security & Validation | `test_security_validation.py` | 401 on unauthenticated protected routes, IDOR 403 across student endpoints, mass assignment on `/auth/me`, no `password_hash` leak, pagination 422 validation, SQLi query safety |
