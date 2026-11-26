# LMS Business Rules & Policies

## 1. Attendance Policy

- **Formula:**
  $$\text{Attendance \%} = \frac{\text{Present Classes}}{\text{Total Eligible Classes}} \times 100$$
- **Class Session Statuses (`class_sessions`):**
  - `held`: Class took place and counts toward eligible classes.
  - `cancelled`: Class was cancelled; **excluded** from the denominator.
  - `holiday`: Institute holiday; **excluded** from the denominator.
- **Student Attendance Statuses (`attendance`):**
  - `Present`: Student attended; counts in numerator and denominator.
  - `Absent`: Student missed class; counts in denominator only.
  - `Approved Leave`: Excused absence; **excluded** from both numerator and denominator.
- **Uniqueness & Audit:**
  - Only one attendance record may exist per `(student_id, batch_id, class_date)`.
  - Bulk attendance updates record an immutable entry in `attendance_audit` capturing `old_status`, `new_status`, `changed_by`, and `changed_at`.

---

## 2. Course Progress & Completion Policy

- **Formula (configurable in `backend/app/config.py`):**
  $$\text{Course Progress \%} = (0.40 \times \text{Lectures \%}) + (0.30 \times \text{Assignments \%}) + (0.30 \times \text{Quizzes \%})$$
  - **Lectures %:** Completed published lectures / Total published lectures in the course $\times 100$ (defaults to `100%` if course has `0` published lectures).
  - **Assignments %:** Submitted or Evaluated assignments / Total assignments in the course (or student's batch) $\times 100$ (defaults to `100%` if `0` assignments).
  - **Quizzes %:** Attempted published quizzes / Total published quizzes in the course (or student's batch) $\times 100$ (defaults to `100%` if `0` quizzes).
- **Course Completion Criteria (configurable in `backend/app/config.py`):**
  A course is marked **Complete** when ALL of the following are satisfied:
  1. `course_progress_pct >= 80.0%` (`COURSE_COMPLETE_MIN_PROGRESS`)
  2. `attendance_pct >= 75.0%` (`COURSE_COMPLETE_MIN_ATTENDANCE`)
  3. All published quizzes for the course/batch have been attempted (`COURSE_COMPLETE_REQUIRE_ALL_QUIZZES = True`).
