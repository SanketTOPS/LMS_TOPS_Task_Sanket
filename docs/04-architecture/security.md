# Security Architecture & Audit Report

**Project:** LMS Project  
**Date:** 2026-11-25  
**Scope:** FastAPI Backend, Authentication, RBAC, IDOR, File Access, Input Validation, Error Handling, Secrets & Database Safety

---

## 1. Security Checklist Results

| # | Security Control | Status | Details & Verification |
|---|---|---|---|
| 1 | **Authentication on Protected Endpoints** | PASS | All `/api/*` endpoints require `get_current_user` or `require_role(...)` except `/api/health`, `/api/auth/login`, `/api/auth/forgot-password`, `/api/auth/reset-password`, and public `/api/certificates/verify/{code}`. Verified by `test_unauthenticated_endpoints_return_401`. |
| 2 | **Role-Based Access Control (RBAC)** | PASS | Admin-only routes (`/api/users`, `/api/payments`, `/api/payments/reports/*`, `/api/batches/{id}/close`, etc.) enforce `require_role(["Admin"])`. Instructor/Admin routes enforce `require_role(["Admin", "Instructor"])`. |
| 3 | **IDOR Protection** | PASS | Students cannot access other students' profiles (`GET /api/students/{id}`), progress (`GET /api/progress/student/{id}`), submissions (`GET /api/submissions/{id}/download`), payment receipts (`GET /api/payments/{id}/receipt`), or certificate PDFs (`GET /api/certificates/{id}/download`). Instructors are scoped to their assigned courses/batches. Verified by `test_idor_student_cannot_access_other_student_records`. |
| 4 | **Private File Access** | PASS | `uploads/` is NOT mounted as public static files. Materials, lecture videos, assignment attachments, submissions, receipts, and certificates are served only via authenticated API endpoints with enrollment/ownership checks. |
| 5 | **File Upload Validation** | PASS | `storage_service.py` validates file extensions, size limits (`MAX_UPLOAD_SIZE_MB = 10`), and magic bytes for uploads, rejecting disallowed or oversized files with `400`/`413`. |
| 6 | **Mass Assignment Protection** | PASS | Pydantic request schemas (e.g., `ProfileUpdateRequest`, `UserUpdateRequest`, `PaymentCreateRequest`) explicitly enumerate allowed fields. `PUT /api/auth/me` cannot escalate `role_id`, `role_name`, or `is_active`. Verified by `test_mass_assignment_and_no_password_hash_leak`. |
| 7 | **Password Hashing & Non-Leakage** | PASS | Passwords hashed with `bcrypt` via `passlib`. `UserResponse` and all user-facing schemas exclude `password_hash`. Verified by `test_valid_login_returns_jwt_without_password_hash` and `test_mass_assignment_and_no_password_hash_leak`. |
| 8 | **Quiz Answer Non-Disclosure** | PASS | Active quiz attempts (`_build_active_attempt_payload`) omit `correct_option_id`. Score and pass/fail are computed strictly server-side in `_finalise_attempt`. |
| 9 | **Error Handling & Information Leakage** | FIXED / PASS | Added a global `Exception` catch-all handler in `backend/app/middleware/error_handler.py` so unhandled exceptions log server-side and return generic `500 INTERNAL_ERROR` JSON without leaking stack traces or SQL details. Login failures return a single generic error message (`Invalid email or password`). |
| 10 | **Secrets Management** | PASS (Dev Note) | No real production secrets or API keys exist in source code. `config.py` uses a development-only fallback for `JWT_SECRET_KEY` (`change-this-to-a-strong-random-secret-key`) which must be overridden via `.env` in production. |
| 11 | **SQL Injection Prevention** | PASS | All database queries use SQLAlchemy 2.0 ORM parameterized `select()` statements. No raw string-interpolated SQL exists. Verified by `test_validation_pagination_and_sqli_safety`. |
| 12 | **CORS Configuration** | PASS | `CORSMiddleware` restricts `allow_origins` to `settings.cors_origins` parsed from `FRONTEND_ORIGIN` (default `http://localhost:5173`), not wildcard `*`. |
| 13 | **Rate Limiting** | PASS | `slowapi` (`SlowAPIMiddleware`) rate-limits authentication endpoints (`/api/auth/login`, `/api/auth/forgot-password`). |
| 14 | **Payment Data & Overpayment Guard** | PASS | Card numbers/CVV are never stored. Overpayments exceeding remaining balance are rejected (`400 OVERPAYMENT_REJECTED`) inside a transaction. |

---

## 2. Fixes Applied During QA & Security Pass

1. **Global Unhandled Exception Handler (`backend/app/middleware/error_handler.py`)**: Added `@app.exception_handler(Exception)` to log exceptions server-side and return a sanitized `{"detail": "An internal server error occurred.", "code": "INTERNAL_ERROR"}` response instead of exposing raw tracebacks when `DEBUG=True`.
2. **Dead Code Removal (`backend/app/services/payment_service.py`, `backend/app/services/certificate_service.py`)**: Removed unused `SessionLocal` and `Batch` local imports inside `_format_payment_response` and `_format_certificate`.
3. **Production Deployment Hardening Recommendation**: Set `DEBUG=False` and a cryptographically random `JWT_SECRET_KEY` (at least 32 bytes) in `.env` before deploying outside local development.
