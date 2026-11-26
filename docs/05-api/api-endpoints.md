# LMS API Endpoints Reference

Base URL: `http://localhost:8000`  
Auth Header: `Authorization: Bearer <access_token>`

## Health
| Method | URL | Roles Allowed | Request Summary | Response Summary | Status Codes |
|---|---|---|---|---|---|
| GET | `/api/health` | Public | - | `{"status": "ok", "app": "LMS API", "env": "..."}` | 200 |

## Auth (`/api/auth`)
| Method | URL | Roles Allowed | Request Summary | Response Summary | Status Codes |
|---|---|---|---|---|---|
| POST | `/api/auth/login` | Public | `{"email", "password"}` | `{"access_token", "token_type", "user"}` | 200, 401, 429 |
| POST | `/api/auth/forgot-password` | Public | `{"email"}` | `{"detail"}` | 200, 429 |
| POST | `/api/auth/reset-password` | Public | `{"token", "new_password"}` | `{"detail"}` | 200, 400 |
| POST | `/api/auth/change-password` | Any Auth | `{"current_password", "new_password"}` | `{"detail"}` | 200, 400, 401 |
| GET | `/api/auth/me` | Any Auth | - | `UserResponse` (no `password_hash`) | 200, 401 |
| PUT | `/api/auth/me` | Any Auth | `{"full_name", "phone"}` | `UserResponse` | 200, 401, 422 |

## Users (`/api/users`)
| Method | URL | Roles Allowed | Request Summary | Response Summary | Status Codes |
|---|---|---|---|---|---|
| POST | `/api/users` | Admin | `{"full_name", "email", "password", "role_name", ...}` | `UserResponse` | 201, 403, 409, 422 |
| GET | `/api/users` | Admin | Query: `page`, `page_size`, `search`, `role` | `PaginatedUsersResponse` | 200, 401, 403, 422 |
| PUT | `/api/users/{user_id}` | Admin | `{"full_name", "email", "phone", "role_name", "is_active"}` | `UserResponse` | 200, 403, 404, 409 |
| PATCH | `/api/users/{user_id}/deactivate` | Admin | - | `UserResponse` | 200, 403, 404 |
| POST | `/api/users/{user_id}/reset-password` | Admin | `{"new_password"}` | `{"detail"}` | 200, 403, 404 |

## Courses & Modules (`/api/courses`)
| Method | URL | Roles Allowed | Request Summary | Response Summary | Status Codes |
|---|---|---|---|---|---|
| GET | `/api/courses` | Any Auth | Query: `page`, `page_size`, `search`, `status` | `PaginatedCoursesResponse` | 200, 401 |
| POST | `/api/courses` | Admin | `{"title", "code", "fee_amount", "instructor_id", ...}` | `CourseResponse` | 201, 403, 409 |
| GET | `/api/courses/{course_id}` | Any Auth | - | `CourseDetailResponse` | 200, 404 |
| PUT | `/api/courses/{course_id}` | Admin, Assigned Instructor | `{"title", "description", ...}` | `CourseResponse` | 200, 403, 404 |
| PATCH | `/api/courses/{course_id}/publish` | Admin | - | `CourseResponse` | 200, 403, 404 |
| PATCH | `/api/courses/{course_id}/archive` | Admin | - | `CourseResponse` | 200, 403, 404 |
| DELETE | `/api/courses/{course_id}` | Admin | - | `204 No Content` | 204, 403, 404, 409 |
| GET/POST/PUT/DELETE | `/api/courses/{course_id}/modules[/{module_id}]` | Auth (read) / Admin, Instructor (write) | `{"title", "sort_order"}` | `CourseModuleResponse` | 200, 201, 204, 403 |

## Batches (`/api/batches`)
| Method | URL | Roles Allowed | Request Summary | Response Summary | Status Codes |
|---|---|---|---|---|---|
| GET | `/api/batches` | Any Auth (role-scoped) | Query: `page`, `page_size`, `course_id` | `PaginatedBatchesResponse` | 200, 401 |
| POST | `/api/batches` | Admin | `{"course_id", "instructor_id", "name", "code", "start_date", "end_date", "max_students"}` | `BatchResponse` | 201, 400, 403 |
| GET | `/api/batches/{batch_id}` | Any Auth (scoped) | - | `BatchResponse` | 200, 403, 404 |
| PUT | `/api/batches/{batch_id}` | Admin | `BatchUpdate` | `BatchResponse` | 200, 403, 404 |
| PATCH | `/api/batches/{batch_id}/close` | Admin | - | `BatchResponse` | 200, 403, 404 |
| PATCH | `/api/batches/{batch_id}/archive` | Admin | - | `BatchResponse` | 200, 403, 404 |
| GET | `/api/batches/{batch_id}/roster` | Admin, Assigned Instructor | - | `BatchRosterResponse` | 200, 403, 404 |
| POST | `/api/batches/{batch_id}/students` | Admin | `{"student_id"}` | `BatchResponse` | 201, 400, 403, 409 |
| DELETE | `/api/batches/{batch_id}/students/{student_id}` | Admin | - | `204 No Content` | 204, 403, 404 |

## Students & Instructors
| Method | URL | Roles Allowed | Request Summary | Response Summary | Status Codes |
|---|---|---|---|---|---|
| GET/POST | `/api/students` | Admin, Instructor (GET) / Admin (POST) | `StudentCreate` | `PaginatedStudentsResponse` / `StudentResponse` | 200, 201, 403 |
| GET/PUT/DELETE | `/api/students/{student_id}` | Admin, Own Student (GET), Batch Instructor (GET) | `StudentUpdate` | `StudentDetailResponse` / `StudentResponse` | 200, 403, 404 |
| GET/POST | `/api/instructors` | Admin | `InstructorCreate` | `PaginatedInstructorsResponse` / `InstructorResponse` | 200, 201, 403 |
| GET | `/api/instructors/me` | Instructor | - | `InstructorResponse` | 200, 403 |
| GET/PUT | `/api/instructors/{instructor_id}` | Admin, Own Instructor | `InstructorUpdate` | `InstructorResponse` | 200, 403, 404 |
| GET | `/api/instructors/{instructor_id}/batches` | Admin, Own Instructor | - | `list[InstructorBatchSummary]` | 200, 403 |
| POST | `/api/instructors/{instructor_id}/assign` | Admin | `{"course_id", "batch_id"}` | `InstructorResponse` | 200, 403, 404 |

## Lectures & Materials
| Method | URL | Roles Allowed | Request Summary | Response Summary | Status Codes |
|---|---|---|---|---|---|
| GET | `/api/courses/{course_id}/lectures` | Enrolled Student, Instructor, Admin | - | `list[LectureResponse]` | 200, 403 |
| GET | `/api/courses/{course_id}/progress` | Enrolled Student, Instructor, Admin | - | `CourseProgressResponse` | 200, 403 |
| POST/PUT/DELETE | `/api/lectures[/{lecture_id}]` | Admin, Assigned Instructor | `LectureCreate` / `LectureUpdate` | `LectureResponse` | 201, 200, 204, 403 |
| POST | `/api/lectures/reorder` | Admin, Assigned Instructor | `{"items": [...]}` | `list[LectureResponse]` | 200, 403 |
| POST/GET | `/api/lectures/{lecture_id}/video` | Instructor/Admin (POST), Enrolled (GET) | Multipart file | `LectureResponse` / File stream | 200, 400, 403 |
| POST | `/api/lectures/{lecture_id}/complete` | Enrolled Student | - | `LectureProgressResponse` | 200, 403 |
| POST | `/api/materials` | Admin, Assigned Instructor | Multipart file + metadata | `StudyMaterialResponse` | 201, 400, 403, 413 |
| GET | `/api/materials/{material_id}/download` | Enrolled Student, Instructor, Admin | - | Binary file stream | 200, 403, 404 |
| DELETE | `/api/materials/{material_id}` | Admin, Assigned Instructor | - | `204 No Content` | 204, 403 |

## Assignments & Submissions
| Method | URL | Roles Allowed | Request Summary | Response Summary | Status Codes |
|---|---|---|---|---|---|
| GET | `/api/assignments` | Any Auth (scoped) | Query: `page`, `page_size`, `course_id`, `batch_id` | `PaginatedAssignmentsResponse` | 200, 401 |
| POST/PUT/DELETE | `/api/assignments[/{assignment_id}]` | Admin, Assigned Instructor | `AssignmentCreate` / `AssignmentUpdate` | `AssignmentResponse` | 201, 200, 204, 403, 409 |
| POST/GET | `/api/assignments/{assignment_id}/attachment` | Instructor/Admin (POST), Scoped Auth (GET) | Multipart file | `AssignmentResponse` / File | 200, 403, 404 |
| GET | `/api/assignments/{assignment_id}/submissions` | Admin, Assigned Instructor, Own Student | - | `list[SubmissionResponse]` | 200, 403 |
| POST | `/api/submissions` | Enrolled Student | Multipart `assignment_id`, `file`, `submission_text` | `SubmissionResponse` | 201, 400, 403 |
| POST | `/api/submissions/{submission_id}/evaluate` | Admin, Assigned Instructor | `{"marks_obtained", "comments"}` | `SubmissionResponse` | 200, 400, 403, 422 |
| GET | `/api/submissions/{submission_id}/download` | Owner Student, Assigned Instructor, Admin | - | Binary file stream | 200, 403, 404 |

## Quizzes & Attempts
| Method | URL | Roles Allowed | Request Summary | Response Summary | Status Codes |
|---|---|---|---|---|---|
| GET/POST | `/api/quizzes` | Scoped Auth (GET), Admin/Instructor (POST) | `QuizCreate` | `PaginatedQuizzesResponse` / `QuizResponse` | 200, 201, 403 |
| GET/PUT/DELETE | `/api/quizzes/{quiz_id}` | Scoped Auth (GET), Admin/Instructor (PUT/DEL) | `QuizUpdate` | `QuizResponse` | 200, 204, 403 |
| GET/POST/PUT/DELETE | `/api/quizzes/{quiz_id}/questions[/{question_id}]` | Admin, Assigned Instructor | Question + options + `correct_option_index` | `QuestionAdminResponse` | 200, 201, 204, 403, 409 |
| GET | `/api/quizzes/{quiz_id}/results` | Admin, Assigned Instructor | - | `list[QuizResultRow]` | 200, 403 |
| POST | `/api/quizzes/{quiz_id}/start` | Enrolled Student | - | `AttemptActiveResponse` (no `correct_option_id`) | 200, 400, 403, 409 |
| GET | `/api/quiz-attempts/{attempt_id}` | Owner Student | - | `AttemptActiveResponse` or `AttemptResultResponse` | 200, 403 |
| PUT | `/api/quiz-attempts/{attempt_id}/answer` | Owner Student | `{"question_id", "selected_option_id"}` | `{"detail"}` | 200, 400, 403 |
| POST | `/api/quiz-attempts/{attempt_id}/submit` | Owner Student | - | `AttemptResultResponse` | 200, 400, 403 |

## Attendance & Progress
| Method | URL | Roles Allowed | Request Summary | Response Summary | Status Codes |
|---|---|---|---|---|---|
| GET | `/api/attendance/roster` | Admin, Assigned Instructor | Query: `batch_id`, `class_date` | `AttendanceRosterResponse` | 200, 403 |
| GET | `/api/attendance/daily` | Admin, Assigned Instructor | Query: `batch_id`, `class_date` | `AttendanceRosterResponse` | 200, 403 |
| POST | `/api/attendance` | Admin, Assigned Instructor | `{"batch_id", "student_id", "class_date", "status"}` | `AttendanceRecordResponse` | 201, 403, 409 |
| POST | `/api/attendance/bulk` | Admin, Assigned Instructor | `{"batch_id", "class_date", "session_status", "records"}` | `AttendanceRosterResponse` | 200, 403 |
| GET | `/api/attendance/me` | Student | Query: `batch_id` (optional) | `StudentAttendanceResponse` | 200, 403 |
| GET | `/api/progress/me` | Student | - | `StudentProgressResponse` | 200, 403 |
| GET | `/api/progress/student/{student_id}` | Admin, Assigned Instructor, Own Student | - | `StudentProgressResponse` | 200, 403, 404 |

## Payments & Certificates
| Method | URL | Roles Allowed | Request Summary | Response Summary | Status Codes |
|---|---|---|---|---|---|
| POST | `/api/payments` | Admin | `{"student_id", "course_id", "amount", "payment_method", "notes"}` | `PaymentResponse` | 201, 400, 403, 404 |
| POST | `/api/payments/{payment_id}/refund` | Admin | `{"reason"}` | `PaymentResponse` | 200, 400, 403, 404 |
| GET | `/api/payments` | Admin | Query: `page`, `page_size`, `student_id`, `course_id`, `status` | `PaginatedPaymentsResponse` | 200, 403 |
| GET | `/api/payments/me` | Student | - | `StudentPaymentsMeResponse` | 200, 403 |
| GET | `/api/payments/reports/student-wise` | Admin | - | `list[StudentFeeReportItem]` | 200, 403 |
| GET | `/api/payments/reports/course-wise` | Admin | - | `list[CourseFeeReportItem]` | 200, 403 |
| GET | `/api/payments/{payment_id}/receipt` | Admin, Owner Student | - | PDF Binary (`application/pdf`) | 200, 403, 404 |
| POST | `/api/certificates/generate` | Student (own), Admin | `{"course_id", "student_id"}` | `CertificateResponse` | 201, 400, 403, 409 |
| GET | `/api/certificates/me` | Student | - | `list[StudentCertificateEligibilityItem]` | 200, 403 |
| GET | `/api/certificates` | Admin | - | `list[CertificateResponse]` | 200, 403 |
| GET | `/api/certificates/verify/{code}` | Public | - | `CertificateVerifyResponse` | 200 |
| GET | `/api/certificates/{certificate_id}/download` | Admin, Owner Student | - | PDF Binary (`application/pdf`) | 200, 403, 404 |
