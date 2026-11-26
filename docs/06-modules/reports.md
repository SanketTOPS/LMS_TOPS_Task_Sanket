# Module Note: Reports

- **Title:** Reports Module
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

- **Purpose:** Provide Admin financial fee collection reports (student-wise and course-wise) and academic progress/quiz result summaries.
- **Roles:** Admin (fee reports, system-wide progress), Instructor (quiz results, batch attendance/progress).
- **Tables:** `payments`, `courses`, `enrollments`, `users`, `quiz_attempts`, `attendance`
- **API Endpoints:** `GET /api/payments/reports/student-wise`, `GET /api/payments/reports/course-wise`, `GET /api/quizzes/{quiz_id}/results`, `GET /api/progress/student/{student_id}`
- **Screens:** `DashboardPage.jsx`, `QuizBuilderPage.jsx` (results tab), `ProgressPage.jsx`
- **Business Rules:** Refunded payments are excluded from `total_collected` / `total_paid`; collection percentage handles zero-fee courses without division-by-zero.
- **Tests:** Verified via `test_payments_certificates.py`, `test_quizzes.py`, and `test_attendance_progress.py`.
- **Known Issues:** Dedicated CSV/Excel export UI for fee reports is planned for v2.
