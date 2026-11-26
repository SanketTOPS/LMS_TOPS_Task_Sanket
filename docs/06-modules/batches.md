# Module Note: Batches & Enrollments

- **Title:** Batches & Enrollments Module
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

- **Purpose:** Organize course deliveries into dated cohorts, manage capacity limits, and enroll students.
- **Roles:** Admin (create, update, close, archive, add/remove students), Assigned Instructor (view roster/batches), Student (view own batches).
- **Tables:** `batches`, `batch_students`, `enrollments`
- **API Endpoints:** `GET/POST /api/batches`, `GET/PUT /api/batches/{batch_id}`, `PATCH /api/batches/{batch_id}/close`, `PATCH /api/batches/{batch_id}/archive`, `GET /api/batches/{batch_id}/roster`, `POST /api/batches/{batch_id}/students`, `DELETE /api/batches/{batch_id}/students/{student_id}`
- **Screens:** `BatchesPage.jsx`, `StudentsPage.jsx`
- **Business Rules:** `end_date >= start_date`; active student count cannot exceed `max_students`; duplicate student enrollment in the same batch is rejected (`409`).
- **Tests:** `backend/tests/test_courses_batches.py` (`test_batch_date_validation`, `test_capacity_limit_and_duplicate_enrollment`, `test_student_cannot_list_other_batches`)
- **Known Issues:** None.
