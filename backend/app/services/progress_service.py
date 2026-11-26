from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.middleware.error_handler import AppException
from app.models import (
    Assignment,
    Batch,
    BatchStudent,
    Course,
    CourseModule,
    Enrollment,
    Instructor,
    Lecture,
    LectureProgress,
    Quiz,
    QuizAttempt,
    Role,
    Submission,
    SubmissionStatus,
    User,
)
from app.services.attendance_service import compute_student_attendance_summary


def get_student_progress(db: Session, student_id: int, current_user: User) -> dict:
    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Student" and current_user.id != student_id:
        raise AppException(403, "You can only view your own progress.", "FORBIDDEN")

    student = db.scalar(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(User.id == student_id, Role.name == "Student")
    )
    if not student:
        raise AppException(404, "Student not found.", "STUDENT_NOT_FOUND")

    if role_name == "Instructor":
        inst_id = db.scalar(select(Instructor.id).where(Instructor.user_id == current_user.id))
        in_inst_batch = db.scalar(
            select(BatchStudent.id)
            .join(Batch, Batch.id == BatchStudent.batch_id)
            .where(
                Batch.instructor_id == inst_id,
                BatchStudent.student_id == student_id,
                BatchStudent.is_active == True,  # noqa: E712
            )
        )
        if not in_inst_batch:
            raise AppException(403, "Student is not in any of your batches.", "FORBIDDEN")

    enr_rows = db.execute(
        select(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .where(Enrollment.student_id == student.id)
        .order_by(Course.title.asc())
    ).all()

    course_items = []
    for enr, course in enr_rows:
        # 1. Lectures %
        pub_lec_ids = list(
            db.scalars(
                select(Lecture.id)
                .join(CourseModule, CourseModule.id == Lecture.module_id)
                .where(CourseModule.course_id == course.id, Lecture.is_published == True)  # noqa: E712
            ).all()
        )
        lec_total = len(pub_lec_ids)
        lec_done = (
            len(
                list(
                    db.scalars(
                        select(LectureProgress.id).where(
                            LectureProgress.student_id == student.id,
                            LectureProgress.lecture_id.in_(pub_lec_ids),
                            LectureProgress.is_completed == True,  # noqa: E712
                        )
                    ).all()
                )
            )
            if lec_total > 0
            else 0
        )
        lec_pct = round((lec_done / lec_total) * 100.0, 2) if lec_total > 0 else 100.0

        # 2. Assignments %
        assign_scope = (Assignment.course_id == course.id) & (
            or_(Assignment.batch_id.is_(None), Assignment.batch_id == enr.batch_id)
            if enr.batch_id
            else Assignment.batch_id.is_(None)
        )
        assign_ids = list(db.scalars(select(Assignment.id).where(assign_scope)).all())
        assign_total = len(assign_ids)
        assign_done = (
            len(
                list(
                    db.scalars(
                        select(Submission.id).where(
                            Submission.student_id == student.id,
                            Submission.assignment_id.in_(assign_ids),
                            Submission.status.in_(
                                [
                                    SubmissionStatus.SUBMITTED,
                                    SubmissionStatus.UNDER_REVIEW,
                                    SubmissionStatus.EVALUATED,
                                    SubmissionStatus.LATE_SUBMISSION,
                                ]
                            ),
                        )
                    ).all()
                )
            )
            if assign_total > 0
            else 0
        )
        assign_pct = round((assign_done / assign_total) * 100.0, 2) if assign_total > 0 else 100.0

        # 3. Quizzes %
        quiz_scope = (Quiz.course_id == course.id) & (Quiz.is_published == True) & (  # noqa: E712
            or_(Quiz.batch_id.is_(None), Quiz.batch_id == enr.batch_id)
            if enr.batch_id
            else Quiz.batch_id.is_(None)
        )
        quiz_ids = list(db.scalars(select(Quiz.id).where(quiz_scope)).all())
        quiz_total = len(quiz_ids)
        attempted_quiz_ids = (
            set(
                db.scalars(
                    select(QuizAttempt.quiz_id).where(
                        QuizAttempt.student_id == student.id,
                        QuizAttempt.quiz_id.in_(quiz_ids),
                        QuizAttempt.submitted_at.is_not(None),
                    )
                ).all()
            )
            if quiz_total > 0
            else set()
        )
        quiz_done = len(attempted_quiz_ids)
        quiz_pct = round((quiz_done / quiz_total) * 100.0, 2) if quiz_total > 0 else 100.0
        all_quizzes_attempted = quiz_done >= quiz_total

        # Weighted progress
        course_progress = round(
            (settings.PROGRESS_WEIGHT_LECTURES * lec_pct)
            + (settings.PROGRESS_WEIGHT_ASSIGNMENTS * assign_pct)
            + (settings.PROGRESS_WEIGHT_QUIZZES * quiz_pct),
            2,
        )

        # Attendance % for this course's batch (if assigned)
        att_summary = compute_student_attendance_summary(db, student.id, batch_id=enr.batch_id)
        att_pct = att_summary["attendance_percentage"]

        is_complete = (
            course_progress >= settings.COURSE_COMPLETE_MIN_PROGRESS
            and att_pct >= settings.COURSE_COMPLETE_MIN_ATTENDANCE
            and (all_quizzes_attempted if settings.COURSE_COMPLETE_REQUIRE_ALL_QUIZZES else True)
        )

        course_items.append(
            {
                "course_id": course.id,
                "course_title": course.title,
                "course_code": course.code,
                "lectures_completed": lec_done,
                "lectures_total": lec_total,
                "lecture_percentage": lec_pct,
                "assignments_submitted": assign_done,
                "assignments_total": assign_total,
                "assignment_percentage": assign_pct,
                "quizzes_attempted": quiz_done,
                "quizzes_total": quiz_total,
                "quiz_percentage": quiz_pct,
                "course_progress_percentage": course_progress,
                "attendance_percentage": att_pct,
                "all_quizzes_attempted": all_quizzes_attempted,
                "is_complete": is_complete,
            }
        )

    overall_prog = (
        round(sum(c["course_progress_percentage"] for c in course_items) / len(course_items), 2)
        if course_items
        else 0.0
    )
    overall_att = compute_student_attendance_summary(db, student.id)["attendance_percentage"]

    return {
        "student_id": student.id,
        "student_name": student.full_name,
        "courses": course_items,
        "overall_progress_percentage": overall_prog,
        "overall_attendance_percentage": overall_att,
    }
