# Software Requirements Specification (SRS) Notes

- **Title:** LMS SRS Notes
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

## 1. Purpose

This document records the scope boundaries, system assumptions, and open product questions for the Role-Based Learning Management System (LMS) built for a training institute.

## 2. System Assumptions

1. **Three Fixed Roles:** Users belong to one of three seeded roles in the `roles` table: `Admin`, `Instructor`, and `Student`. Self-registration is disabled; Admins create or onboard all accounts.
2. **Batch-Based Delivery:** Courses (`courses`) are delivered to cohorts called Batches (`batches`). Students enroll into a course and are assigned to a batch (`enrollments`, `batch_students`).
3. **Server as Source of Truth:** Deadlines, late submission flags, quiz timers, quiz scores, attendance percentages, payment balances, and certificate eligibility are computed strictly on the backend.
4. **Private Assets:** Uploaded study materials, videos, assignment attachments, student submissions, fee receipts, and certificates are private and served only after authentication and role/ownership checks.
5. **Manual Payments (v1):** Fee payments (`payments`) are recorded manually by Admins (Cash, UPI, Bank Transfer, Card reference); no live payment gateway webhook or card storage is included in v1.

## 3. In Scope (v1)

- Role-based JWT authentication, password reset flow, and profile management (`users`, `roles`)
- Course and module management (`courses`, `course_modules`)
- Batch management, capacity limits, and student roster assignment (`batches`, `batch_students`, `enrollments`)
- Lecture sequencing, video/material upload & download, and completion tracking (`lectures`, `study_materials`, `lecture_progress`)
- Assignments with file upload, versioned resubmissions, late flags, and instructor evaluation (`assignments`, `submissions`, `submission_versions`, `assignment_feedback`)
- Timed MCQ quizzes with auto-finalisation, anti-leak question payloads, and post-submit review (`quizzes`, `questions`, `quiz_options`, `quiz_attempts`, `quiz_answers`)
- Daily/bulk attendance with class session status (`held`, `cancelled`, `holiday`) and audit trail (`attendance`, `attendance_audit`, `class_sessions`)
- Weighted course progress and completion eligibility (`40%` lectures + `30%` assignments + `30%` quizzes)
- Manual fee payment tracking, refunds, PDF receipts, and student/course reports (`payments`)
- PDF certificate generation and public verification lookup (`certificates`)

## 4. Out of Scope (v1)

- Live online payment gateway integration (Stripe/Razorpay checkout)
- Real-time video conferencing (Zoom/WebRTC) or live chat
- Automated email/SMS delivery service (password reset tokens and notifications are persisted/returned without external SMTP)
- Multi-tenant institute isolation

## 5. Open Questions

1. **Notifications & Announcements UI:** Database tables `notifications` and `announcements` exist in `communication.py`; should v2 expose dedicated REST endpoints and a notification bell UI?
2. **Dedicated Payments & Certificates Frontend Pages:** Backend endpoints and PDF generation are complete under `/api/payments` and `/api/certificates`; confirm whether dedicated frontend pages for Payments, Certificates, and public `/verify/:code` should be prioritized in the next UI sprint.
3. **Email Provider Selection:** Which transactional email provider (SendGrid, SES, Resend) will be wired to `forgot-password` and announcement notifications in v2?
