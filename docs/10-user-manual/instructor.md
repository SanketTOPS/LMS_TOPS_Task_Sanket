# Instructor User Manual

- **Title:** Instructor User Manual
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

## 1. Dashboard & Assigned Batches
1. Sign in at `/login` to view `/dashboard`.
2. Open **Courses** (`/courses`) or **Batches** (`/batches`) to see your assigned courses and active student rosters.

`[screenshot: instructor-dashboard]`

## 2. Managing Lectures & Study Materials (`/courses/:courseId/manage-lectures`)
1. Open your course and click **Manage Lectures**.
2. Create modules and lectures, reorder lectures, and upload lecture videos (`.mp4`, `.webm`, `.mov`) or study materials (`.pdf`, `.ppt`, `.pptx`, `.docx`, `.zip`).

`[screenshot: manage-lectures]`

## 3. Creating & Evaluating Assignments (`/assignments`)
1. Go to **Assignments** and click **Create Assignment** (title, description, max marks, course/batch, due date, optional attachment).
2. Click **View Submissions** on an assignment to review student uploads.
3. Click **Evaluate**, enter marks (`0` to `max_marks`) and feedback comments, and save.

`[screenshot: evaluate-submission-modal]`

## 4. Building Quizzes & Viewing Results (`/quizzes`, `/quizzes/:quizId/builder`)
1. Go to **Quizzes** and create a quiz with time limit, passing marks, availability window, and `allow_retake` setting.
2. Open **Quiz Builder** to add MCQ questions, options, marks, and mark the single correct option.
3. Publish the quiz and review student scores in the **Results** table.

`[screenshot: quiz-builder]`

## 5. Marking Attendance & Checking Progress (`/attendance`, `/progress`)
1. Go to **Attendance**, select your **Batch** and **Class Date**, and choose session status (`held`, `cancelled`, or `holiday`).
2. Toggle each student as **Present**, **Absent**, or **Approved Leave**, then click **Save Attendance**.
3. Use **Students** (`/students`) and **Progress** (`/progress`) to monitor student completion metrics.

`[screenshot: instructor-attendance-roster]`
