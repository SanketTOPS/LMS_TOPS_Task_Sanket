# Module Note: Lectures & Study Materials

- **Title:** Lectures & Study Materials Module
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

- **Purpose:** Deliver ordered video/text lectures and downloadable study materials, and track student lecture completion.
- **Roles:** Admin / Assigned Instructor (CRUD, reorder, upload video/materials), Enrolled Student (stream/download, mark complete).
- **Tables:** `lectures`, `study_materials`, `lecture_progress`
- **API Endpoints:** `GET /api/courses/{course_id}/lectures`, `GET /api/courses/{course_id}/progress`, `POST/PUT/DELETE /api/lectures`, `POST /api/lectures/reorder`, `POST/GET /api/lectures/{lecture_id}/video`, `POST /api/lectures/{lecture_id}/complete`, `POST /api/materials`, `GET /api/materials/{material_id}/download`, `DELETE /api/materials/{material_id}`
- **Screens:** `InstructorLecturesPage.jsx`, `StudentLecturePage.jsx`
- **Business Rules:** Unenrolled students receive `403`; `POST /api/lectures/{id}/complete` is idempotent; uploads validate extension, `MAX_UPLOAD_SIZE_MB`, and magic bytes.
- **Tests:** `backend/tests/test_lectures_materials.py` (2 tests passing)
- **Known Issues:** None.
