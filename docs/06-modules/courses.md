# Module Note: Courses & Modules

- **Title:** Courses & Modules
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

- **Purpose:** Manage course catalog, fee amounts, publish/archive lifecycle, and ordered curriculum modules.
- **Roles:** Admin (create, publish, archive, delete), Assigned Instructor (update, manage modules), Student (view published/enrolled).
- **Tables:** `courses`, `course_modules`, `instructors`
- **API Endpoints:** `GET/POST /api/courses`, `GET/PUT/DELETE /api/courses/{course_id}`, `PATCH /api/courses/{course_id}/publish`, `PATCH /api/courses/{course_id}/archive`, `GET/POST /api/courses/{course_id}/modules`, `PUT/DELETE /api/courses/{course_id}/modules/{module_id}`
- **Screens:** `CoursesPage.jsx`, `CourseDetailPage.jsx`, `InstructorsPage.jsx`
- **Business Rules:** Unique course `code`; instructors can only edit courses assigned to them; deleting a course with batches/assignments/quizzes is restricted by FK constraints.
- **Tests:** `backend/tests/test_courses_batches.py` (`test_instructor_cannot_edit_unassigned_course`)
- **Known Issues:** None.
