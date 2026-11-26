# Use Cases & User Stories

- **Title:** LMS Use Cases & User Stories
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

## 1. Actors

| Actor | Description |
|---|---|
| **Admin** | Manages users, courses, batches, enrollments, fee payments, reports, and system-wide certificates. |
| **Instructor** | Manages assigned course lectures/materials, assignments, quizzes, evaluations, and batch attendance. |
| **Student** | Consumes lectures/materials, submits assignments, attempts quizzes, tracks attendance/progress, views fees, and downloads certificates. |
| **Public Verifier** | Unauthenticated visitor verifying a certificate using its unique `verification_code`. |

---

## 2. Core Use Cases

1. **UC-01 Authenticate & Manage Profile:** Login via `/api/auth/login`, change password, update profile (`/api/auth/me`).
2. **UC-02 Manage Users & Roles (Admin):** Create, update, deactivate users and reset passwords (`/api/users`).
3. **UC-03 Manage Courses & Batches (Admin / Instructor):** Create/publish courses, add modules, create batches, enroll students within `max_students`.
4. **UC-04 Deliver & Complete Lectures (Instructor / Student):** Upload videos/study materials, mark lectures complete (`/api/lectures/{id}/complete`).
5. **UC-05 Assignment Lifecycle (Instructor / Student):** Create assignments, submit files with version history, evaluate marks and feedback.
6. **UC-06 Timed MCQ Quiz (Instructor / Student):** Build quiz questions, start timed attempt, auto-save answers, submit or auto-expire, review results.
7. **UC-07 Attendance & Progress Tracking (Instructor / Student):** Mark bulk attendance with `class_sessions` status (`held`/`cancelled`/`holiday`), view weighted progress.
8. **UC-08 Fee Payments & Receipts (Admin / Student):** Record installments, prevent overpayment, issue refunds, download PDF receipts.
9. **UC-09 Certificate Generation & Verification (Student / Admin / Public):** Generate PDF certificate when completion rules pass; verify via `/api/certificates/verify/{code}`.

---

## 3. User Stories & Acceptance Criteria

### Admin Stories
- **US-A1 (User Lifecycle):** As an Admin, I want to create and deactivate users so only active staff and students can log in.
  - *Acceptance:* Duplicate email returns `409`; deactivated user login is rejected; `password_hash` is never returned in API responses.
- **US-A2 (Payment Recording & Overpayment Guard):** As an Admin, I want to record fee payments and refunds so student balances stay accurate.
  - *Acceptance:* Partial payments set status to `Partially Paid`; full balance sets `Paid`; overpayment is rejected (`400`); refund requires a reason and updates pending balance.

### Instructor Stories
- **US-I1 (Assignment Evaluation):** As an Instructor, I want to grade submissions for my batches so students receive marks and feedback.
  - *Acceptance:* Marks `> max_marks` or `< 0` are rejected; status transitions to `Evaluated`; instructors cannot grade courses they are not assigned to (`403`).
- **US-I2 (Bulk Attendance):** As an Instructor, I want to mark daily attendance for a batch and mark holidays/cancelled days so attendance percentages stay fair.
  - *Acceptance:* `cancelled`, `holiday`, and `Approved Leave` are excluded from the attendance denominator; every update writes a row to `attendance_audit`.

### Student Stories
- **US-S1 (Timed Quiz Attempt):** As a Student, I want to take an active quiz with a countdown timer and see my score after submission.
  - *Acceptance:* Questions omit `correct_option_id` before submission; duplicate attempts are blocked unless `allow_retake=true`; expired attempts auto-finalise server-side.
- **US-S2 (Certificate Download):** As a Student, I want to generate and download my course certificate once I meet completion criteria.
  - *Acceptance:* Blocked (`400`) if progress `< 80%`, attendance `< 75%`, or quizzes remain unattempted; duplicate generation returns `409`; generates PDF with unique `LMS-YYYY-XXXXXXXX` and `VER-...` code.
