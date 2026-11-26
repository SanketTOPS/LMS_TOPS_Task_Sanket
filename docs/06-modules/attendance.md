# Module Note: Attendance & Progress

- **Title:** Attendance & Progress Module
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

- **Purpose:** Track daily batch attendance with audit history, and compute weighted course progress and completion eligibility.
- **Roles:** Admin / Assigned Instructor (view roster, mark single/bulk attendance, view student progress), Student (view own attendance summary and progress).
- **Tables:** `attendance`, `attendance_audit`, `class_sessions`, `lecture_progress`
- **API Endpoints:** `GET /api/attendance/roster`, `GET /api/attendance/daily`, `POST /api/attendance`, `POST /api/attendance/bulk`, `GET /api/attendance/me`, `GET /api/progress/me`, `GET /api/progress/student/{student_id}`
- **Screens:** `AttendancePage.jsx`, `ProgressPage.jsx`
- **Business Rules & Formulas:**
  - `Attendance % = Present / Total Eligible Classes * 100` (excludes `cancelled` sessions, `holiday` sessions, and `Approved Leave`).
  - Unique `(batch_id, student_id, class_date)`; every change writes to `attendance_audit`.
  - `Course Progress % = 0.40 * lectures_pct + 0.30 * assignments_pct + 0.30 * quizzes_pct`.
  - Course is complete when `progress >= 80%`, `attendance >= 75%`, and all published quizzes are attempted.
- **Tests:** `backend/tests/test_attendance_progress.py` (2 tests passing)
- **Known Issues:** None.
