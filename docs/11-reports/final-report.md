# Final Project Report

- **Title:** Role-Based Learning Management System (LMS) — Final Report
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

## 1. Objectives Achieved

- Delivered a full-stack, role-based LMS supporting **Admin**, **Instructor**, and **Student** workflows.
- Enforced server-side integrity across deadlines, quiz timers/scoring, attendance denominators, payment balances, and certificate eligibility.
- Implemented private file handling with magic-byte validation and environment-switchable local/Cloudinary storage.
- Verified backend behavior with a 30-test automated Pytest suite and documented deployment for Vercel, Render, and Managed MySQL.

## 2. Architecture Summary

- **Frontend:** React 18 + Vite + Tailwind CSS SPA (`frontend/`), deployed via Vercel with `vercel.json` SPA rewrites.
- **Backend:** FastAPI + SQLAlchemy 2.0 + Alembic (`backend/`), deployed via Render (`Procfile` + `uvicorn`).
- **Database:** MySQL 8.x in production; SQLite in-memory for isolated Pytest runs.
- **Storage:** `LocalStorageBackend` (`dev`) and `CloudinaryStorageBackend` (`prod`, authenticated private assets).

## 3. Modules Delivered

1. Auth & Users (`auth.py`, `users.py`)
2. Courses & Batches (`courses.py`, `batches.py`, `students.py`, `instructors.py`)
3. Lectures & Study Materials (`lectures.py`, `materials.py`)
4. Assignments & Submissions (`assignments.py`)
5. Quizzes & Attempts (`quizzes.py`)
6. Attendance & Progress (`attendance.py`, `progress.py`)
7. Payments & Certificates (`payments.py`, `certificates.py`)

## 4. Testing Outcome

- **Backend Pytest Suite:** `30 passed, 0 failed, 0 errors` (31.62s) covering auth, RBAC, IDOR, mass assignment, file validation, assignments, quizzes, attendance, payments, certificates, and SQLi/pagination safety. See [test-report.md](../08-testing/test-report.md).

## 5. Deployment Details

- **Frontend:** Vercel (`VITE_API_BASE_URL` pointing to Render `/api`)
- **Backend:** Render (`alembic upgrade head` pre-deploy + `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, health check `/api/health`)
- **Database:** Managed MySQL 8.x with `mysqldump` backup policy ([backup-restore.md](../09-deployment/backup-restore.md))

## 6. Limitations & Learnings

- **Limitations:** Dedicated frontend UI pages for Payments/Certificates/Public Verification and Notifications/Announcements REST endpoints are deferred to v2 (backend payment/certificate APIs and DB tables are ready). Local MySQL and Node.js were not available in this test sandbox, so `alembic upgrade head` and `npm run build` must be run in the target environment.
- **Learnings:** Keeping business rules (quiz scoring, late flags, progress formulas, overpayment checks) strictly in backend service functions and pairing `require_role` with resource-level ownership checks eliminates client-side tampering and IDOR risks.
