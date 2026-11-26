# Live Demo Script & Seeded Accounts

- **Title:** LMS Demo Script
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

## 1. Seeded Test Accounts (`backend/app/seed.py`)

Run `python -m app.seed` inside `backend/` before starting the demo. All seeded accounts use password: `Password@123`.

| Role | Name | Email | Password |
|---|---|---|---|
| **Admin** | Aarav Mehta | `admin@institute.edu` | `Password@123` |
| **Instructor 1** | Ananya Sharma | `ananya.sharma@institute.edu` | `Password@123` |
| **Instructor 2** | Rohan Verma | `rohan.verma@institute.edu` | `Password@123` |
| **Student 1** | Priya Nair | `student1@institute.edu` | `Password@123` |
| **Student 2** | Kabir Patel | `student2@institute.edu` | `Password@123` |

---

## 2. Recommended Demo Order (10 Minutes)

1. **Health & Auth (1 min):** Show `GET /api/health` (`200 OK`, `database: connected`). Log in as Admin (`admin@institute.edu`) on `/login`.
2. **Admin Management (2 min):** Open `/admin/users` (show RBAC & user lifecycle), `/courses` (`FSWD-101`), and `/batches` (batch roster & capacity).
3. **Instructor Workflow (3 min):** Log in as `ananya.sharma@institute.edu`.
   - Open `/courses/:id/manage-lectures` to show module/lecture ordering and materials.
   - Open `/assignments` to show submissions and the **Evaluate** modal.
   - Open `/attendance` to mark a batch date as `held` or `cancelled` and save bulk attendance.
4. **Student Workflow (3 min):** Log in as `student1@institute.edu`.
   - Open `/courses/:id/learn` and mark a lecture complete.
   - Open `/quizzes`, start a timed quiz on `/quiz-attempts/:attemptId`, show live timer and answer review on `/quiz-attempts/:attemptId/result`.
   - Open `/attendance` and `/progress` to show the `40/30/30` weighted progress bars and completion checklist.
5. **Payments & Certificates API / Swagger or Postman (1 min):** Demonstrate `POST /api/payments`, receipt PDF download, `POST /api/certificates/generate`, and public `GET /api/certificates/verify/{code}`.
