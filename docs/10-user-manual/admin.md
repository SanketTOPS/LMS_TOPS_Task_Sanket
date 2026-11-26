# Admin User Manual

- **Title:** Admin User Manual
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

## 1. Logging In
1. Open `/login` and enter your Admin email and password.
2. Click **Sign In** to open `/dashboard`.

`[screenshot: admin-dashboard]`

## 2. Managing Users (`/admin/users`)
1. Click **Users** in the left sidebar.
2. Click **Create User**, enter full name, email, temporary password, and select role (`Admin`, `Instructor`, or `Student`).
3. Use **Deactivate** to block a user from logging in without deleting historical records, or **Reset Password** to set a new password.

`[screenshot: admin-users-management]`

## 3. Creating Courses & Batches (`/courses`, `/batches`)
1. Go to **Courses** -> **Create Course**, enter title, unique code (e.g. `FSWD-101`), fee amount, and assign an instructor.
2. Click **Publish** when ready for student enrollment.
3. Go to **Batches** -> **Create Batch**, select the course, instructor, start/end dates, and `max_students`.
4. Open a batch's **Roster** to add or remove students (capacity `max_students` is enforced).

`[screenshot: courses-and-batches]`

## 4. Recording Fee Payments & Refunds (API `/api/payments`)
1. Send `POST /api/payments` with `student_id`, `course_id`, `amount`, `payment_method`, and `notes`.
2. Status is automatically derived as `Partially Paid` or `Paid`. Overpayments are rejected.
3. To refund a payment, use `POST /api/payments/{payment_id}/refund` with a mandatory `reason`.
4. View fee reports via `GET /api/payments/reports/student-wise` and `GET /api/payments/reports/course-wise`.

## 5. Certificates & Verification (`/api/certificates`)
1. View all issued certificates via `GET /api/certificates`.
2. Generate a certificate for an eligible student via `POST /api/certificates/generate` with `student_id` and `course_id`.
3. Download any certificate PDF via `GET /api/certificates/{id}/download`.
