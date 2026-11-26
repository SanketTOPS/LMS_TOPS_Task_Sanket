# Module Note: Notifications & Announcements

- **Title:** Notifications & Announcements Module
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

- **Purpose:** Persist user notifications and batch/institute announcements.
- **Roles:** Admin / Instructor (target audience), Student (recipient).
- **Tables:** `notifications`, `announcements` (`backend/app/models/communication.py`)
- **API Endpoints:** Schema/model foundation present; dedicated REST endpoints and UI bell planned for v2.
- **Screens:** `Toast.jsx` handles in-app transient feedback in v1.
- **Business Rules:** Notifications track `is_read` per `user_id`; announcements support optional `course_id` / `batch_id` scoping.
- **Tests:** Covered indirectly via `Base.metadata.create_all()` schema tests.
- **Known Issues:** REST router and frontend notification center are deferred to v2.
