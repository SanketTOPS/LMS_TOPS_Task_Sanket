# Changelog

- **Title:** LMS Changelog
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

> **Note:** Git history is unavailable because `.git` is not initialized in this directory. Replace `[commit-ref: ...]` with actual commit hashes once committed.

## [1.0.0] - 2026-11-25
### Added
- **Auth & Users:** JWT login, forgot/reset/change password, profile endpoints, Admin user CRUD & deactivation (`[commit-ref: pending]`)
- **Courses, Batches & Lectures:** Course/module/batch lifecycle, roster management, lecture videos, private study material downloads (`[commit-ref: pending]`)
- **Assignments & Quizzes:** Submission version history, server-side late detection, evaluation workflow, timed MCQ quizzes with anti-leak payloads and auto-finalisation (`[commit-ref: pending]`)
- **Attendance & Progress:** `class_sessions` (`held`/`cancelled`/`holiday`), `attendance_audit`, weighted progress (`40/30/30`), completion gate (`[commit-ref: pending]`)
- **Payments & Certificates:** Installments, overpayment rejection, refunds, ReportLab PDF receipts/certificates, public verification endpoint (`[commit-ref: pending]`)
- **QA & Deployment:** Global 500 exception sanitizer, `test_security_validation.py` (30/30 Pytest passing), `CloudinaryStorageBackend`, `Procfile`, `vercel.json`, pinned `requirements.txt`, deployment & API docs (`[commit-ref: pending]`)
