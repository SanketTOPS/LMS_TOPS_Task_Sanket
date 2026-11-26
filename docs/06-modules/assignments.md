# Module Note: Assignments & Submissions

- **Title:** Assignments & Submissions Module
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

- **Purpose:** Manage course/batch assignments, versioned student file submissions, late flags, and instructor grading.
- **Roles:** Admin / Assigned Instructor (create, update, delete, upload attachment, evaluate), Enrolled Student (view, download attachment, submit/resubmit, view own feedback).
- **Tables:** `assignments`, `submissions`, `submission_versions`, `assignment_feedback`
- **API Endpoints:** `GET/POST /api/assignments`, `GET/PUT/DELETE /api/assignments/{assignment_id}`, `POST/GET /api/assignments/{assignment_id}/attachment`, `GET /api/assignments/{assignment_id}/submissions`, `POST /api/submissions`, `POST /api/submissions/{submission_id}/evaluate`, `GET /api/submissions/{submission_id}/download`
- **Screens:** `AssignmentsPage.jsx`
- **Business Rules:** Delete blocked (`409`) if submissions exist; `Submitted` vs `Late Submission` computed server-side from `due_date`; resubmissions saved in `submission_versions` until `Evaluated`; marks validated `0 <= marks <= max_marks`.
- **Tests:** `backend/tests/test_assignments.py` (2 tests passing)
- **Known Issues:** None.
