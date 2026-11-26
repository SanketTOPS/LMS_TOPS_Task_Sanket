# LMS Test Report

**Execution Date:** 2026-11-25  
**Command:** `backend\venv\Scripts\pytest.exe backend\tests -v --tb=short`  
**Result:** **30 passed, 0 failed, 0 errors** (1 deprecation warning from `fastapi.testclient`, 32.73s)

---

## Test Results Table

| Test ID | Module | Steps | Expected | Actual | Status |
|---|---|---|---|---|---|
| TC-01 | Health | `GET /api/health` | HTTP 200 with `status: ok` | Passed | PASS |
| TC-02 | Auth & Users | `POST /api/auth/login` with valid credentials | HTTP 200, JWT returned, `password_hash` omitted | Passed | PASS |
| TC-03 | Auth & Users | `POST /api/auth/login` with wrong email or wrong password | Generic `Invalid email or password` error on both | Passed | PASS |
| TC-04 | Auth & Users | `POST /api/auth/login` for deactivated user | Login blocked (401/403) | Passed | PASS |
| TC-05 | Auth & Users | Call `/api/auth/me` with expired JWT | HTTP 401 rejected | Passed | PASS |
| TC-06 | Auth & Users | Student calls Admin `/api/users` endpoint | HTTP 403 Forbidden | Passed | PASS |
| TC-07 | Auth & Users | Admin creates user with existing email | HTTP 409 Conflict | Passed | PASS |
| TC-08 | Auth & Users | `PUT /api/auth/me` and `POST /api/auth/change-password` | Profile updated; login works with new password | Passed | PASS |
| TC-09 | Auth & Users | Admin creates, updates, deactivates, resets password | Lifecycle operations succeed | Passed | PASS |
| TC-10 | Courses & Batches | Create batch with `end_date < start_date` | HTTP 400/422 validation error | Passed | PASS |
| TC-11 | Courses & Batches | Enroll beyond `max_students` or duplicate enrollment | Capacity limit & duplicate blocked (400/409) | Passed | PASS |
| TC-12 | Courses & Batches | Instructor updates unassigned course | HTTP 403 Forbidden | Passed | PASS |
| TC-13 | Courses & Batches | Student lists batches | Only assigned batches returned | Passed | PASS |
| TC-14 | Lectures & Materials | Unenrolled student reads lectures; enrolled marks complete twice | Unenrolled 403; completion idempotent | Passed | PASS |
| TC-15 | Lectures & Materials | Upload disallowed extension or oversized file | Rejected (400/413) | Passed | PASS |
| TC-16 | Assignments | Submit past due date and resubmit | `Late Submission` flagged server-side; version history kept | Passed | PASS |
| TC-17 | Assignments | Evaluate with marks > `max_marks`; student lists other submissions | Marks > max rejected (400/422); student isolated | Passed | PASS |
| TC-18 | Quizzes | Start attempt, inspect questions, submit, retry without retake | `correct_option_id` absent before submit; score computed server-side; duplicate blocked | Passed | PASS |
| TC-19 | Quizzes | Start outside window; submit after timer expiry | Outside window blocked; expired attempt auto-finalised | Passed | PASS |
| TC-20 | Attendance & Progress | Mark held, cancelled, holiday, and approved leave sessions | Cancelled/holiday/leave excluded from denominator | Passed | PASS |
| TC-21 | Attendance & Progress | Duplicate attendance insert; student attempts to post attendance | Duplicate blocked (409); student 403 | Passed | PASS |
| TC-22 | Payments & Certificates | Pay $400 then $600 on $1000 course; download receipt | `Partially Paid` -> `Paid`; valid `%PDF-` receipt returned | Passed | PASS |
| TC-23 | Payments & Certificates | Pay $250 when $200 remaining | Rejected (400/409) with overpayment message | Passed | PASS |
| TC-24 | Payments & Certificates | Refund $1000 payment, then attempt second refund | Status `Refunded`, balance $1000 pending; second refund 400 | Passed | PASS |
| TC-25 | Payments & Certificates | Student calls `POST /api/payments` | HTTP 403 Forbidden | Passed | PASS |
| TC-26 | Payments & Certificates | Generate cert before vs after eligibility; duplicate; verify | Ineligible 400; eligible 201 + PDF; duplicate 409; public verify works | Passed | PASS |
| TC-27 | Security & Validation | Call 11 protected GET endpoints without token | All return HTTP 401 | Passed | PASS |
| TC-28 | Security & Validation | Student A requests Student B profile, progress, receipt, cert | All return HTTP 403 (IDOR blocked) | Passed | PASS |
| TC-29 | Security & Validation | `PUT /api/auth/me` with `role_id=1`; `GET /api/users` | Role remains `Student`; `password_hash` absent | Passed | PASS |
| TC-30 | Security & Validation | `page=0`, `page_size=500`, SQLi string in `q` parameter | Pagination returns 422; SQLi returns 200 with `[]` | Passed | PASS |
