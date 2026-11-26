# Viva Preparation Guide

- **Title:** LMS Technical Viva Preparation
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

## 1. Request-to-Response Walkthroughs

### A. Login (`POST /api/auth/login`)
1. `SlowAPIMiddleware` checks rate limit on `/api/auth/login`.
2. `auth.py` validates `LoginRequest` (`email`, `password`) via Pydantic.
3. `auth_service.authenticate_user()` queries `users` by email, verifies `password` against `user.password_hash` using `bcrypt`, and checks `user.is_active`. Both missing user and wrong password return the same generic error (`Invalid email or password`) to prevent account enumeration.
4. `security.create_access_token()` signs an HS256 JWT containing `sub` (user ID), `role`, and `exp`.
5. `TokenResponse` serializes `UserResponse`, which explicitly excludes `password_hash`.

### B. Quiz Submit (`POST /api/quiz-attempts/{attempt_id}/submit`)
1. `quizzes.py` authenticates the Student via `require_role(["Student"])`.
2. `quiz_service.submit_quiz_attempt()` verifies `attempt.student_id == current_user.id`.
3. `_auto_finalise_if_expired()` checks if `now > started_at + time_limit_minutes + TIMER_GRACE_SECONDS`; if expired, it finalises using only answers already saved in `quiz_answers` before expiry.
4. `_finalise_attempt()` loads `questions` and saved `quiz_answers`, compares `selected_option_id == question.correct_option_id`, sets `is_correct`, sums `question.marks` into `attempt.score`, computes `attempt.is_passed = score >= quiz.passing_marks`, sets `submitted_at`, and commits.
5. Returns `AttemptResultResponse` (only now including `correct_option_id` for review).

### C. Attendance Percentage (`compute_student_attendance_summary`)
1. `attendance_service.py` queries `class_sessions` for the student's batch(es) and excludes sessions marked `cancelled` or `holiday`.
2. Queries `attendance` rows for the student; rows with status `Approved Leave` are also excluded from the eligible denominator.
3. Formula: `Present / (Present + Absent) * 100` (where `Late` or other rules follow `policies.md`, and cancelled/holiday/approved leave are excluded).

### D. Payment Status Derivation (`POST /api/payments` & `POST /api/payments/{id}/refund`)
1. `payments.py` restricts access to `Admin` via `require_role(["Admin"])`.
2. Inside `with db.begin_nested():`, `payment_service.record_payment()` sums existing `Paid` / `Partially Paid` payments for `(student_id, course_id)`.
3. Computes `outstanding = total_fee - currently_paid`. If `amount > outstanding`, raises `400 OVERPAYMENT_REJECTED`.
4. Derives status: `Paid` if `currently_paid + amount >= total_fee`, else `Partially Paid`, and generates a unique `RCP-YYYY-XXXXXXXX` receipt number.
5. On refund, status becomes `Refunded` (requires `reason`), reducing `total_paid` and restoring pending balance.

### E. Certificate Generation (`POST /api/certificates/generate`)
1. `certificates.py` allows `Student` (own) or `Admin` (specifying `student_id`).
2. `certificate_service.generate_certificate()` checks `certificates` for `(student_id, course_id)` — if present, raises `409 DUPLICATE_CERTIFICATE`.
3. Calls `progress_service.get_student_progress()` and verifies `is_complete == True` (`progress >= 80%`, `attendance >= 75%`, and `all_quizzes_attempted == True`). Otherwise raises `400 NOT_ELIGIBLE_FOR_CERTIFICATE`.
4. Generates `LMS-YYYY-XXXXXXXX` and `VER-...`, renders PDF via `reportlab` (`pdf_generator.py`), saves via `get_storage_backend()`, and inserts into `certificates`.

---

## 2. Database Relationships Summary

- `roles (1) -> (N) users (1) -> (0..1) instructors`
- `instructors (1) -> (N) courses (1) -> (N) course_modules (1) -> (N) lectures`
- `courses (1) -> (N) batches (1) -> (N) batch_students <- (N) users`
- `users (1) -> (N) enrollments -> (1) courses` (with optional `batch_id`)
- `courses/batches (1) -> (N) assignments (1) -> (N) submissions (1) -> (N) submission_versions & assignment_feedback`
- `courses/batches (1) -> (N) quizzes (1) -> (N) questions (1) -> (N) quiz_options`
- `quizzes (1) -> (N) quiz_attempts (1) -> (N) quiz_answers`
- `batches (1) -> (N) class_sessions` & `attendance (1) -> (N) attendance_audit`
- `users + courses -> payments` & `certificates`

---

## 3. Authorization Logic

Two layers work together:
1. **Route-level RBAC (`dependencies/auth.py`):** `get_current_user` validates the JWT and active status; `require_role(["Admin", "Instructor"])` blocks unauthorized roles with `403`.
2. **Service-level Resource Checks:** Prevents IDOR even when a role is allowed on the endpoint (e.g., `student_service.get_student_detail`, `progress_service.get_student_progress`, `assignment_service.resolve_submission_download`, `certificate_service.get_certificate_download` verify ownership for Students and batch/course assignment for Instructors).

---

## 4. 25 Likely Viva Questions & Short Answers

1. **Why FastAPI?** Async support, automatic Pydantic request/response validation, dependency injection for auth/DB, and clean OpenAPI schemas.
2. **How are passwords stored?** Hashed with `bcrypt` via `passlib` (`security.py`); plain passwords are never stored or logged.
3. **How do you prevent password hash leakage?** `UserResponse` in `schemas/user.py` explicitly defines output fields and omits `password_hash`.
4. **How does `require_role` work?** It's a FastAPI dependency factory wrapping `get_current_user` that checks `current_user.role.name in allowed_roles` and raises `403` otherwise.
5. **What is IDOR and how did you prevent it?** Insecure Direct Object Reference; prevented by checking `record.student_id == current_user.id` (for Students) and batch/course assignment (for Instructors) in services.
6. **Why not serve `uploads/` as static files?** Static mounts bypass auth checks; serving files through authenticated endpoints enforces enrollment and ownership rules.
7. **How do you validate uploaded files?** `storage_service.py` checks allowed extensions, `MAX_UPLOAD_SIZE_MB`, non-empty size, and magic byte signatures (`MAGIC_SIGNATURES`).
8. **How does file storage work in production on Render?** `STORAGE_BACKEND=cloudinary` switches `get_storage_backend()` to `CloudinaryStorageBackend` using signed `authenticated` uploads/downloads.
9. **Why keep `submission_versions`?** To preserve full resubmission history (timestamp, file, status) until an assignment is `Evaluated`.
10. **How is `Late Submission` determined?** Server compares `datetime.now(timezone.utc)` against `assignment.due_date` during `POST /api/submissions`.
11. **How do you prevent quiz cheating before submission?** `_build_active_attempt_payload()` excludes `correct_option_id` from question payloads until `submitted_at` is set.
12. **What happens if a student's quiz timer expires without clicking Submit?** `_auto_finalise_if_expired()` auto-finalises the attempt using answers saved before expiry when fetched or submitted.
13. **How is course progress calculated?** `0.40 * lecture_pct + 0.30 * assignment_pct + 0.30 * quiz_pct` (`config.py` constants).
14. **When is a course marked complete?** Progress `>= 80%`, attendance `>= 75%`, and all published quizzes attempted (`progress_service.py`).
15. **How are cancelled classes and holidays handled in attendance?** Stored in `class_sessions` (`cancelled`/`holiday`) and excluded from the denominator along with `Approved Leave`.
16. **How is attendance tampering audited?** Every upsert in `attendance_service.py` inserts an audit record into `attendance_audit` (who changed what and when).
17. **How is overpayment prevented?** Inside `with db.begin_nested():`, `payment_service.py` sums existing non-refunded payments and rejects amounts exceeding `total_fee - currently_paid` (`400`).
18. **How are PDF receipts and certificates generated?** Dynamically rendered using `reportlab` in `backend/app/utils/pdf_generator.py`.
19. **How does public certificate verification work safely?** `GET /api/certificates/verify/{code}` is public and returns only limited fields (`valid`, `student_name`, `course_title`, `issued_at`).
20. **How is SQL injection prevented?** All queries use SQLAlchemy 2.0 ORM parameterized `select()` expressions; no raw string-interpolated SQL.
21. **How is mass assignment prevented?** Pydantic schemas accept only explicit allowed fields (e.g., `ProfileUpdateRequest` only accepts `full_name` and `phone`).
22. **How are unhandled 500 errors handled?** `error_handler.py` catches `Exception`, logs it server-side, and returns a generic `INTERNAL_ERROR` JSON without stack traces.
23. **How is rate limiting implemented?** `slowapi` (`SlowAPIMiddleware`) rate-limits `/api/auth/login` and `/api/auth/forgot-password`.
24. **Why SQLite in-memory for Pytest and MySQL in production?** SQLite in-memory makes the 30-test suite fast and self-contained in CI/local dev, while Alembic + PyMySQL manage production MySQL 8.x.
25. **How does Vercel handle React Router SPA refreshes?** `frontend/vercel.json` rewrites `/(.*)` to `/index.html`.
