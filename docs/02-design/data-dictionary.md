# LMS Database Data Dictionary

All tables include `created_at` (`DATETIME`, server default `CURRENT_TIMESTAMP`, NOT NULL) and `updated_at` (`DATETIME`, server default `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`, NOT NULL).

## Delete Behaviour Policy

- **Soft Delete:** `users` (`is_active`), `courses` (`status = 'archived'`), and `batches` (`status = 'archived'`) use soft deletion instead of physical row removal.
- **`RESTRICT`:** Used on all foreign keys where dependent business, academic, or financial records exist (e.g., enrollments, submissions, payments, attendance, certificates).
- **`CASCADE`:** Used **only** for owned child rows (`quiz_options.question_id`, `quiz_answers.attempt_id`, `quiz_answers.question_id`, `quiz_answers.selected_option_id`).
- **`SET NULL`:** Used on `questions.correct_option_id` to break the circular FK with `quiz_options` safely.

---

## 1. `roles`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Role identifier | — |
| `name` | `VARCHAR(50)` | UNIQUE, IX | `NOT NULL` | Role name (`Admin`, `Instructor`, `Student`) | — |
| `description` | `VARCHAR(255)` | — | `NULL` | Role description | — |

## 2. `users`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | User identifier | Soft delete (`is_active`) |
| `role_id` | `INT` | FK, IX | `NOT NULL`, FK -> `roles.id` | Assigned role | `RESTRICT` |
| `full_name` | `VARCHAR(120)` | — | `NOT NULL` | User full name | — |
| `email` | `VARCHAR(255)` | UNIQUE, IX | `NOT NULL` | Login email address | — |
| `password_hash` | `VARCHAR(255)` | — | `NOT NULL` | Bcrypt password hash | — |
| `phone` | `VARCHAR(30)` | — | `NULL` | Contact phone number | — |
| `is_active` | `BOOLEAN` | IX | `NOT NULL`, default `TRUE` | Active/soft-delete flag | — |

## 3. `instructors`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Instructor profile ID | — |
| `user_id` | `INT` | FK, UNIQUE, IX | `NOT NULL`, FK -> `users.id` | Linked user account | `RESTRICT` |
| `bio` | `TEXT` | — | `NULL` | Instructor biography | — |
| `expertise` | `VARCHAR(255)` | — | `NULL` | Subject-matter areas | — |
| `qualification` | `VARCHAR(255)` | — | `NULL` | Academic qualification | — |
| `experience_years` | `INT` | — | `NOT NULL`, default `0` | Years of teaching experience | — |
| `is_active` | `BOOLEAN` | IX | `NOT NULL`, default `TRUE` | Active flag | — |

## 4. `courses`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Course ID | Soft delete (`archived`) |
| `title` | `VARCHAR(200)` | — | `NOT NULL` | Course title | — |
| `code` | `VARCHAR(50)` | UNIQUE, IX | `NOT NULL` | Unique course code | — |
| `description` | `TEXT` | — | `NULL` | Course syllabus summary | — |
| `duration_weeks` | `INT` | — | `NOT NULL`, default `4` | Course duration in weeks | — |
| `fee_amount` | `DECIMAL(10,2)` | — | `NOT NULL`, default `0.00` | Standard course fee | — |
| `status` | `ENUM` | IX | `NOT NULL`, `draft \| published \| archived` | Lifecycle status | — |
| `created_by` | `INT` | FK, IX | `NOT NULL`, FK -> `users.id` | Creator user ID | `RESTRICT` |

## 5. `course_modules`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Module ID | — |
| `course_id` | `INT` | FK, IX | `NOT NULL`, FK -> `courses.id` | Parent course | `RESTRICT` |
| `title` | `VARCHAR(200)` | — | `NOT NULL` | Module title | — |
| `description` | `TEXT` | — | `NULL` | Module overview | — |
| `sort_order` | `INT` | — | `NOT NULL`, default `1` | Display order | — |

## 6. `batches`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Batch ID | Soft delete (`archived`) |
| `course_id` | `INT` | FK, IX | `NOT NULL`, FK -> `courses.id` | Associated course | `RESTRICT` |
| `instructor_id` | `INT` | FK, IX | `NOT NULL`, FK -> `instructors.id` | Assigned instructor | `RESTRICT` |
| `name` | `VARCHAR(150)` | — | `NOT NULL` | Batch display name | — |
| `code` | `VARCHAR(50)` | UNIQUE, IX | `NOT NULL` | Unique batch code | — |
| `start_date` | `DATE` | — | `NOT NULL` | Batch start date | — |
| `end_date` | `DATE` | — | `NULL` | Batch end date | — |
| `schedule_info` | `VARCHAR(255)` | — | `NULL` | Days/time schedule | — |
| `max_students` | `INT` | — | `NOT NULL`, default `30` | Seat capacity | — |
| `status` | `ENUM` | IX | `NOT NULL`, `upcoming \| active \| closed \| archived` | Batch status | — |

## 7. `batch_students`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Mapping ID | — |
| `batch_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `batches.id` | Batch ID | `RESTRICT` |
| `student_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `users.id` | Student user ID | `RESTRICT` |
| `joined_at` | `DATETIME` | — | `NOT NULL`, default `NOW()` | Date joined batch | — |
| `is_active` | `BOOLEAN` | — | `NOT NULL`, default `TRUE` | Active membership flag | — |
| *Unique* | — | UQ | `(batch_id, student_id)` | Prevents duplicate batch assignment | — |

## 8. `enrollments`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Enrollment ID | — |
| `student_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `users.id` | Student user ID | `RESTRICT` |
| `course_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `courses.id` | Course ID | `RESTRICT` |
| `batch_id` | `INT` | FK, IX | `NULL`, FK -> `batches.id` | Assigned batch | `RESTRICT` |
| `enrolled_at` | `DATETIME` | — | `NOT NULL`, default `NOW()` | Enrollment timestamp | — |
| `status` | `ENUM` | IX | `NOT NULL`, `active \| completed \| dropped` | Enrollment status | — |
| *Unique* | — | UQ | `(student_id, course_id)` | Prevents duplicate enrollment | — |

## 9. `lectures`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Lecture ID | — |
| `module_id` | `INT` | FK, IX | `NOT NULL`, FK -> `course_modules.id` | Parent module | `RESTRICT` |
| `batch_id` | `INT` | FK, IX | `NULL`, FK -> `batches.id` | Optional batch scope | `RESTRICT` |
| `title` | `VARCHAR(200)` | — | `NOT NULL` | Lecture title | — |
| `description` | `TEXT` | — | `NULL` | Lecture summary | — |
| `video_url` | `VARCHAR(500)` | — | `NULL` | Video URL (no binary) | — |
| `duration_minutes` | `INT` | — | `NOT NULL`, default `0` | Duration in minutes | — |
| `sort_order` | `INT` | — | `NOT NULL`, default `1` | Sequence order | — |
| `is_published` | `BOOLEAN` | — | `NOT NULL`, default `TRUE` | Visibility flag | — |
| `created_by` | `INT` | FK, IX | `NOT NULL`, FK -> `users.id` | Creator user ID | `RESTRICT` |

## 10. `study_materials`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Material ID | — |
| `course_id` | `INT` | FK, IX | `NOT NULL`, FK -> `courses.id` | Parent course | `RESTRICT` |
| `module_id` | `INT` | FK, IX | `NULL`, FK -> `course_modules.id` | Optional module | `RESTRICT` |
| `lecture_id` | `INT` | FK, IX | `NULL`, FK -> `lectures.id` | Optional lecture | `RESTRICT` |
| `title` | `VARCHAR(200)` | — | `NOT NULL` | Material title | — |
| `file_name` | `VARCHAR(255)` | — | `NOT NULL` | Original file name | — |
| `file_url` | `VARCHAR(500)` | — | `NOT NULL` | Storage URL (metadata only) | — |
| `file_size_bytes` | `INT` | — | `NOT NULL`, default `0` | File size in bytes | — |
| `mime_type` | `VARCHAR(100)` | — | `NULL` | MIME type | — |
| `uploaded_by` | `INT` | FK, IX | `NOT NULL`, FK -> `users.id` | Uploader user ID | `RESTRICT` |

## 11. `assignments`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Assignment ID | — |
| `course_id` | `INT` | FK, IX | `NOT NULL`, FK -> `courses.id` | Parent course | `RESTRICT` |
| `batch_id` | `INT` | FK, IX | `NULL`, FK -> `batches.id` | Optional batch | `RESTRICT` |
| `module_id` | `INT` | FK, IX | `NULL`, FK -> `course_modules.id` | Optional module | `RESTRICT` |
| `title` | `VARCHAR(200)` | — | `NOT NULL` | Assignment title | — |
| `description` | `TEXT` | — | `NULL` | Instructions | — |
| `attachment_name` | `VARCHAR(255)` | — | `NULL` | Prompt attachment name | — |
| `attachment_url` | `VARCHAR(500)` | — | `NULL` | Prompt attachment URL | — |
| `max_marks` | `DECIMAL(6,2)` | — | `NOT NULL`, default `100.00` | Maximum score | — |
| `due_date` | `DATETIME` | IX | `NOT NULL` | Submission deadline | — |
| `allow_late` | `BOOLEAN` | — | `NOT NULL`, default `FALSE` | Late submission flag | — |
| `created_by` | `INT` | FK, IX | `NOT NULL`, FK -> `users.id` | Creator user ID | `RESTRICT` |

## 12. `submissions`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Submission ID | — |
| `assignment_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `assignments.id` | Target assignment | `RESTRICT` |
| `student_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `users.id` | Student user ID | `RESTRICT` |
| `submission_text` | `TEXT` | — | `NULL` | Text answer | — |
| `file_name` | `VARCHAR(255)` | — | `NULL` | Submitted file name | — |
| `file_url` | `VARCHAR(500)` | — | `NULL` | Submitted file URL | — |
| `file_size_bytes` | `INT` | — | `NOT NULL`, default `0` | File size in bytes | — |
| `submitted_at` | `DATETIME` | — | `NULL` | Submission timestamp | — |
| `marks_obtained` | `DECIMAL(6,2)` | — | `NULL` | Awarded score | — |
| `status` | `ENUM` | IX | `NOT NULL`, `Pending \| Submitted \| Under Review \| Evaluated \| Late Submission` | Review status | — |
| *Unique* | — | UQ | `(assignment_id, student_id)` | One submission per student/assignment | — |

## 13. `assignment_feedback`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Feedback ID | — |
| `submission_id` | `INT` | FK, IX | `NOT NULL`, FK -> `submissions.id` | Target submission | `RESTRICT` |
| `instructor_id` | `INT` | FK, IX | `NOT NULL`, FK -> `users.id` | Reviewer user ID | `RESTRICT` |
| `comments` | `TEXT` | — | `NOT NULL` | Evaluation remarks | — |
| `marks_awarded` | `DECIMAL(6,2)` | — | `NULL` | Marks recorded with feedback | — |

## 14. `quizzes`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Quiz ID | — |
| `course_id` | `INT` | FK, IX | `NOT NULL`, FK -> `courses.id` | Parent course | `RESTRICT` |
| `batch_id` | `INT` | FK, IX | `NULL`, FK -> `batches.id` | Optional batch | `RESTRICT` |
| `title` | `VARCHAR(200)` | — | `NOT NULL` | Quiz title | — |
| `description` | `TEXT` | — | `NULL` | Quiz instructions | — |
| `time_limit_minutes` | `INT` | — | `NOT NULL`, default `30` | Duration limit | — |
| `passing_marks` | `DECIMAL(6,2)` | — | `NOT NULL`, default `0.00` | Passing threshold | — |
| `total_marks` | `DECIMAL(6,2)` | — | `NOT NULL`, default `0.00` | Total quiz marks | — |
| `allow_retake` | `BOOLEAN` | — | `NOT NULL`, default `FALSE` | Enables multiple attempts | — |
| `max_attempts` | `INT` | — | `NOT NULL`, default `1` | Max attempts allowed | — |
| `is_published` | `BOOLEAN` | IX | `NOT NULL`, default `FALSE` | Published flag | — |
| `created_by` | `INT` | FK, IX | `NOT NULL`, FK -> `users.id` | Author user ID | `RESTRICT` |

## 15. `questions`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Question ID | — |
| `quiz_id` | `INT` | FK, IX | `NOT NULL`, FK -> `quizzes.id` | Parent quiz | `RESTRICT` |
| `question_text` | `TEXT` | — | `NOT NULL` | Question prompt | — |
| `marks` | `DECIMAL(6,2)` | — | `NOT NULL`, default `1.00` | Marks for question | — |
| `sort_order` | `INT` | — | `NOT NULL`, default `1` | Display order | — |
| `correct_option_id` | `INT` | FK | `NULL`, FK -> `quiz_options.id` | Correct option stored separately | `SET NULL` |

## 16. `quiz_options`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Option ID | — |
| `question_id` | `INT` | FK, IX | `NOT NULL`, FK -> `questions.id` | Parent question | `CASCADE` |
| `option_text` | `VARCHAR(500)` | — | `NOT NULL` | Choice text | — |
| `sort_order` | `INT` | — | `NOT NULL`, default `1` | Display order | — |

## 17. `quiz_attempts`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Attempt ID | — |
| `quiz_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `quizzes.id` | Quiz ID | `RESTRICT` |
| `student_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `users.id` | Student user ID | `RESTRICT` |
| `attempt_number` | `INT` | UQ | `NOT NULL`, default `1` | Sequential attempt (`1` unless retake enabled) | — |
| `started_at` | `DATETIME` | — | `NOT NULL`, default `NOW()` | Start time | — |
| `submitted_at` | `DATETIME` | — | `NULL` | Submission time | — |
| `score` | `DECIMAL(6,2)` | — | `NOT NULL`, default `0.00` | Achieved score | — |
| `is_passed` | `BOOLEAN` | — | `NOT NULL`, default `FALSE` | Pass/fail indicator | — |
| *Unique* | — | UQ | `(quiz_id, student_id, attempt_number)` | Enforces unique attempt numbering | — |

## 18. `quiz_answers`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Answer ID | — |
| `attempt_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `quiz_attempts.id` | Parent attempt | `CASCADE` |
| `question_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `questions.id` | Question ID | `CASCADE` |
| `selected_option_id` | `INT` | FK | `NULL`, FK -> `quiz_options.id` | Selected option | `CASCADE` |
| `is_correct` | `BOOLEAN` | — | `NOT NULL`, default `FALSE` | Graded correctness | — |
| *Unique* | — | UQ | `(attempt_id, question_id)` | One answer per question per attempt | — |

## 19. `attendance`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Attendance ID | — |
| `student_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `users.id` | Student user ID | `RESTRICT` |
| `batch_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `batches.id` | Batch ID | `RESTRICT` |
| `class_date` | `DATE` | IX, UQ | `NOT NULL` | Session date | — |
| `status` | `ENUM` | IX | `NOT NULL`, `Present \| Absent` | Attendance status | — |
| `marked_by` | `INT` | FK, IX | `NOT NULL`, FK -> `users.id` | Marker user ID | `RESTRICT` |
| `remarks` | `VARCHAR(255)` | — | `NULL` | Optional notes | — |
| *Unique* | — | UQ | `(student_id, batch_id, class_date)` | Prevents duplicate daily attendance | — |

## 20. `lecture_progress`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Progress ID | — |
| `student_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `users.id` | Student user ID | `RESTRICT` |
| `lecture_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `lectures.id` | Lecture ID | `RESTRICT` |
| `is_completed` | `BOOLEAN` | — | `NOT NULL`, default `FALSE` | Completion flag | — |
| `watched_seconds` | `INT` | — | `NOT NULL`, default `0` | Playback position | — |
| `completed_at` | `DATETIME` | — | `NULL` | Completion timestamp | — |
| *Unique* | — | UQ | `(student_id, lecture_id)` | One progress row per student/lecture | — |

## 21. `certificates`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Certificate ID | — |
| `student_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `users.id` | Student user ID | `RESTRICT` |
| `course_id` | `INT` | FK, IX, UQ | `NOT NULL`, FK -> `courses.id` | Course ID | `RESTRICT` |
| `batch_id` | `INT` | FK, IX | `NULL`, FK -> `batches.id` | Optional batch | `RESTRICT` |
| `certificate_number` | `VARCHAR(100)` | UNIQUE, IX | `NOT NULL` | Unique certificate serial | — |
| `issued_at` | `DATETIME` | — | `NOT NULL`, default `NOW()` | Issue timestamp | — |
| `file_name` | `VARCHAR(255)` | — | `NULL` | PDF file name | — |
| `file_url` | `VARCHAR(500)` | — | `NULL` | PDF download URL | — |
| `issued_by` | `INT` | FK, IX | `NOT NULL`, FK -> `users.id` | Issuer user ID | `RESTRICT` |
| *Unique* | — | UQ | `(student_id, course_id)` | One certificate per student/course | — |

## 22. `payments`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Payment ID | — |
| `student_id` | `INT` | FK, IX | `NOT NULL`, FK -> `users.id` | Student user ID | `RESTRICT` |
| `course_id` | `INT` | FK, IX | `NOT NULL`, FK -> `courses.id` | Course ID | `RESTRICT` |
| `enrollment_id` | `INT` | FK, IX | `NULL`, FK -> `enrollments.id` | Related enrollment | `RESTRICT` |
| `amount_due` | `DECIMAL(10,2)` | — | `NOT NULL` | Total fee due | — |
| `amount_paid` | `DECIMAL(10,2)` | — | `NOT NULL`, default `0.00` | Amount paid | — |
| `payment_method` | `VARCHAR(50)` | — | `NULL` | e.g., UPI, Card, Cash | — |
| `transaction_ref` | `VARCHAR(120)` | IX | `NULL` | External reference ID | — |
| `status` | `ENUM` | IX | `NOT NULL`, `Paid \| Partially Paid \| Pending \| Failed \| Refunded` | Payment status | — |
| `paid_at` | `DATETIME` | — | `NULL` | Payment timestamp | — |
| `recorded_by` | `INT` | FK, IX | `NULL`, FK -> `users.id` | Staff who recorded payment | `RESTRICT` |
| `notes` | `TEXT` | — | `NULL` | Remarks | — |

## 23. `notifications`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Notification ID | — |
| `user_id` | `INT` | FK, IX | `NOT NULL`, FK -> `users.id` | Recipient user ID | `RESTRICT` |
| `title` | `VARCHAR(200)` | — | `NOT NULL` | Notification heading | — |
| `message` | `TEXT` | — | `NOT NULL` | Notification body | — |
| `is_read` | `BOOLEAN` | IX | `NOT NULL`, default `FALSE` | Read status | — |
| `link_url` | `VARCHAR(500)` | — | `NULL` | Target route/URL | — |

## 24. `announcements`
| Column | Type | Key | Constraints | Description | Delete Behaviour |
|---|---|---|---|---|---|
| `id` | `INT` | PK | `AUTO_INCREMENT` | Announcement ID | — |
| `course_id` | `INT` | FK, IX | `NULL`, FK -> `courses.id` | Optional course scope | `RESTRICT` |
| `batch_id` | `INT` | FK, IX | `NULL`, FK -> `batches.id` | Optional batch scope | `RESTRICT` |
| `title` | `VARCHAR(200)` | — | `NOT NULL` | Announcement title | — |
| `content` | `TEXT` | — | `NOT NULL` | Announcement body | — |
| `created_by` | `INT` | FK, IX | `NOT NULL`, FK -> `users.id` | Author user ID | `RESTRICT` |
| `is_active` | `BOOLEAN` | IX | `NOT NULL`, default `TRUE` | Active visibility flag | — |
