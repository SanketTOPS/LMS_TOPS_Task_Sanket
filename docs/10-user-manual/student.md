# Student User Manual

- **Title:** Student User Manual
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

## 1. Dashboard & Profile (`/dashboard`, `/profile`)
1. Sign in at `/login` with your student email and password.
2. Update your display name, phone number, or password anytime under **Profile** (`/profile`).

`[screenshot: student-dashboard]`

## 2. Watching Lectures & Downloading Materials (`/courses/:courseId/learn`)
1. Open **Courses** (`/courses`), select an enrolled course, and click **Start Learning**.
2. Watch lecture videos, download attached study materials, and click **Mark Complete** to update your course progress.

`[screenshot: student-lecture-player]`

## 3. Submitting Assignments (`/assignments`)
1. Open **Assignments** to view assigned work, instructions, reference attachments, and the deadline countdown.
2. Upload your solution file before the due date to receive `Submitted` status (late uploads are flagged `Late Submission`).
3. You may resubmit updated versions until your instructor marks the submission `Evaluated`.

`[screenshot: student-assignments]`

## 4. Taking Timed Quizzes (`/quizzes`, `/quiz-attempts/:attemptId`)
1. Open **Quizzes** to view available quizzes within their active time window.
2. Click **Start Quiz** to launch the attempt page with the live server-synced countdown timer.
3. Selecting an option auto-saves your answer. Click **Submit Quiz** when finished (or let the timer auto-submit saved answers).
4. Review your score, pass/fail status, and correct answers on `/quiz-attempts/:attemptId/result`.

`[screenshot: quiz-attempt-page]`

## 5. Attendance, Progress & Certificates (`/attendance`, `/progress`)
1. Open **Attendance** to view your monthly summary and attendance percentage (cancelled classes, holidays, and approved leaves are excluded).
2. Open **Progress** to inspect your lecture, assignment, and quiz completion bars (`>= 80%` progress, `>= 75%` attendance, and all quizzes attempted unlock certificate eligibility).
3. Download fee receipts (`/api/payments/{id}/receipt`) and eligible certificates (`/api/certificates/{id}/download`).

`[screenshot: student-progress-page]`
