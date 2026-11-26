# Module Note: Quizzes & Attempts

- **Title:** Quizzes & Attempts Module
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

- **Purpose:** Timed MCQ assessments with server-side scoring, window enforcement, and post-submission answer review.
- **Roles:** Admin / Assigned Instructor (quiz & question CRUD, view results), Enrolled Student (list available, start attempt, save answer, submit, review).
- **Tables:** `quizzes`, `questions`, `quiz_options`, `quiz_attempts`, `quiz_answers`
- **API Endpoints:** `GET/POST /api/quizzes`, `GET/PUT/DELETE /api/quizzes/{quiz_id}`, `GET/POST/PUT/DELETE /api/quizzes/{quiz_id}/questions`, `GET /api/quizzes/{quiz_id}/results`, `POST /api/quizzes/{quiz_id}/start`, `GET /api/quiz-attempts/{attempt_id}`, `PUT /api/quiz-attempts/{attempt_id}/answer`, `POST /api/quiz-attempts/{attempt_id}/submit`
- **Screens:** `QuizzesPage.jsx`, `QuizBuilderPage.jsx`, `QuizAttemptPage.jsx`, `QuizResultPage.jsx`
- **Business Rules:** Duplicate attempts blocked unless `allow_retake=true`; `correct_option_id` omitted before submission; `score` and `is_passed` computed server-side; expired attempts auto-finalised using saved answers.
- **Tests:** `backend/tests/test_quizzes.py` (2 tests passing)
- **Known Issues:** None.
