# Module Note: Certificates

- **Title:** Certificates Module
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

- **Purpose:** Issue unique PDF course completion certificates when academic criteria are met, and provide public verification.
- **Roles:** Student (generate/download own), Admin (generate for student, list all, download), Public (verify by code).
- **Tables:** `certificates`, `courses`, `enrollments`, `users`
- **API Endpoints:** `POST /api/certificates/generate`, `GET /api/certificates/me`, `GET /api/certificates`, `GET /api/certificates/{certificate_id}/download`, `GET /api/certificates/verify/{code}`
- **Screens:** API-ready in v1 (dedicated frontend page & public `/verify/:code` route planned for v2)
- **Business Rules:** Blocked (`400`) unless `progress_service` reports `is_complete == True`; unique `(student_id, course_id)` (`409` on duplicate); generates unique `LMS-YYYY-XXXXXXXX` and `VER-...`; ReportLab PDF rendered with student name, course, and date.
- **Tests:** `backend/tests/test_payments_certificates.py` (`test_certificate_blocked_when_ineligible_and_generated_when_eligible`)
- **Known Issues:** Requires Alembic migration `e738c8b6a123` on live MySQL (`verification_code` column).
