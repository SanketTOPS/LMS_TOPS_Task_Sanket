from datetime import datetime, timedelta, timezone
from decimal import Decimal
import math

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.middleware.error_handler import AppException
from app.models import (
    Batch,
    BatchStudent,
    Course,
    Enrollment,
    Instructor,
    Question,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizOption,
    User,
)
from app.schemas.quiz import QuestionCreate, QuestionUpdate, QuizCreate, QuizUpdate
from app.services.lecture_service import ensure_course_read_access, ensure_course_write_access

TIMER_GRACE_SECONDS = 30


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _ensure_student_quiz_access(db: Session, quiz: Quiz, student_id: int) -> None:
    if not quiz.is_published:
        raise AppException(403, "This quiz is not published.", "FORBIDDEN")
    if quiz.batch_id is not None:
        in_batch = db.scalar(
            select(BatchStudent.id).where(
                BatchStudent.batch_id == quiz.batch_id,
                BatchStudent.student_id == student_id,
                BatchStudent.is_active == True,  # noqa: E712
            )
        )
        if not in_batch:
            raise AppException(403, "You are not enrolled in this quiz's batch.", "FORBIDDEN")
    else:
        enrolled = db.scalar(
            select(Enrollment.id).where(
                Enrollment.course_id == quiz.course_id,
                Enrollment.student_id == student_id,
            )
        )
        if not enrolled:
            raise AppException(403, "You are not enrolled in this quiz's course.", "FORBIDDEN")


def _serialize_quiz(db: Session, q: Quiz, student_id: int | None = None) -> dict:
    course_title = db.scalar(select(Course.title).where(Course.id == q.course_id))
    batch_name = db.scalar(select(Batch.name).where(Batch.id == q.batch_id)) if q.batch_id else None
    question_count = db.scalar(select(func.count(Question.id)).where(Question.quiz_id == q.id)) or 0

    my_attempts_count = 0
    latest_attempt_id = None
    latest_attempt_submitted = False
    if student_id is not None:
        attempts = list(
            db.scalars(
                select(QuizAttempt)
                .where(QuizAttempt.quiz_id == q.id, QuizAttempt.student_id == student_id)
                .order_by(QuizAttempt.attempt_number.desc())
            ).all()
        )
        my_attempts_count = len(attempts)
        if attempts:
            latest_attempt_id = attempts[0].id
            latest_attempt_submitted = attempts[0].submitted_at is not None

    return {
        "id": q.id,
        "course_id": q.course_id,
        "course_title": course_title,
        "batch_id": q.batch_id,
        "batch_name": batch_name,
        "title": q.title,
        "description": q.description,
        "time_limit_minutes": q.time_limit_minutes,
        "passing_marks": q.passing_marks,
        "total_marks": q.total_marks,
        "allow_retake": q.allow_retake,
        "max_attempts": q.max_attempts,
        "available_from": q.available_from,
        "available_until": q.available_until,
        "is_published": q.is_published,
        "question_count": question_count,
        "created_by": q.created_by,
        "created_at": q.created_at,
        "updated_at": q.updated_at,
        "my_attempts_count": my_attempts_count,
        "latest_attempt_id": latest_attempt_id,
        "latest_attempt_submitted": latest_attempt_submitted,
    }


def list_quizzes(
    db: Session,
    current_user: User,
    *,
    course_id: int | None = None,
    batch_id: int | None = None,
    within_window: bool = False,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    role_name = current_user.role.name if current_user.role else ""
    stmt = select(Quiz)
    count_stmt = select(func.count(Quiz.id))

    if role_name == "Instructor":
        inst_id = db.scalar(select(Instructor.id).where(Instructor.user_id == current_user.id))
        if not inst_id:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        inst_course_ids = select(Course.id).where(Course.instructor_id == inst_id)
        inst_batch_ids = select(Batch.id).where(Batch.instructor_id == inst_id)
        scope = or_(Quiz.course_id.in_(inst_course_ids), Quiz.batch_id.in_(inst_batch_ids))
        stmt = stmt.where(scope)
        count_stmt = count_stmt.where(scope)
    elif role_name == "Student":
        my_course_ids = select(Enrollment.course_id).where(Enrollment.student_id == current_user.id)
        my_batch_ids = select(BatchStudent.batch_id).where(
            BatchStudent.student_id == current_user.id,
            BatchStudent.is_active == True,  # noqa: E712
        )
        scope = (Quiz.is_published == True) & (  # noqa: E712
            or_(
                Quiz.batch_id.in_(my_batch_ids),
                (Quiz.batch_id.is_(None)) & (Quiz.course_id.in_(my_course_ids)),
            )
        )
        stmt = stmt.where(scope)
        count_stmt = count_stmt.where(scope)

    if within_window:
        now = datetime.now(timezone.utc)
        win_filter = (
            (Quiz.available_from.is_(None) | (Quiz.available_from <= now))
            & (Quiz.available_until.is_(None) | (Quiz.available_until >= now))
        )
        stmt = stmt.where(win_filter)
        count_stmt = count_stmt.where(win_filter)

    if course_id is not None:
        stmt = stmt.where(Quiz.course_id == course_id)
        count_stmt = count_stmt.where(Quiz.course_id == course_id)
    if batch_id is not None:
        stmt = stmt.where(Quiz.batch_id == batch_id)
        count_stmt = count_stmt.where(Quiz.batch_id == batch_id)

    stmt = stmt.order_by(desc(Quiz.created_at))
    total = db.scalar(count_stmt) or 0
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    offset = (page - 1) * page_size

    rows = list(db.scalars(stmt.offset(offset).limit(page_size)).all())
    stu_id = current_user.id if role_name == "Student" else None
    return {
        "items": [_serialize_quiz(db, q, student_id=stu_id) for q in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def create_quiz(db: Session, payload: QuizCreate, current_user: User) -> dict:
    ensure_course_write_access(db, payload.course_id, current_user)
    if payload.batch_id is not None:
        batch = db.scalar(select(Batch).where(Batch.id == payload.batch_id))
        if not batch or batch.course_id != payload.course_id:
            raise AppException(400, "Batch does not belong to the specified course.", "INVALID_BATCH")

    quiz = Quiz(
        course_id=payload.course_id,
        batch_id=payload.batch_id,
        title=payload.title.strip(),
        description=payload.description,
        time_limit_minutes=payload.time_limit_minutes,
        passing_marks=payload.passing_marks,
        total_marks=payload.total_marks,
        allow_retake=payload.allow_retake,
        max_attempts=payload.max_attempts if payload.allow_retake else 1,
        available_from=payload.available_from,
        available_until=payload.available_until,
        is_published=payload.is_published,
        created_by=current_user.id,
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return _serialize_quiz(db, quiz)


def get_quiz(db: Session, quiz_id: int, current_user: User) -> dict:
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise AppException(404, "Quiz not found.", "QUIZ_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Student":
        _ensure_student_quiz_access(db, quiz, current_user.id)
        return _serialize_quiz(db, quiz, student_id=current_user.id)

    ensure_course_read_access(db, quiz.course_id, current_user)
    return _serialize_quiz(db, quiz)


def update_quiz(db: Session, quiz_id: int, payload: QuizUpdate, current_user: User) -> dict:
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise AppException(404, "Quiz not found.", "QUIZ_NOT_FOUND")
    ensure_course_write_access(db, quiz.course_id, current_user)

    new_from = payload.available_from if payload.available_from is not None else quiz.available_from
    new_until = payload.available_until if payload.available_until is not None else quiz.available_until
    if new_from is not None and new_until is not None and _to_utc(new_until) <= _to_utc(new_from):
        raise AppException(422, "available_until must be strictly after available_from.", "INVALID_WINDOW")

    for field in (
        "batch_id",
        "title",
        "description",
        "time_limit_minutes",
        "passing_marks",
        "total_marks",
        "allow_retake",
        "max_attempts",
        "available_from",
        "available_until",
        "is_published",
    ):
        val = getattr(payload, field)
        if val is not None:
            setattr(quiz, field, val.strip() if isinstance(val, str) and field == "title" else val)

    if not quiz.allow_retake:
        quiz.max_attempts = 1

    db.commit()
    db.refresh(quiz)
    return _serialize_quiz(db, quiz)


def delete_quiz(db: Session, quiz_id: int, current_user: User) -> None:
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise AppException(404, "Quiz not found.", "QUIZ_NOT_FOUND")
    ensure_course_write_access(db, quiz.course_id, current_user)

    has_attempts = db.scalar(select(QuizAttempt.id).where(QuizAttempt.quiz_id == quiz_id)) is not None
    if has_attempts:
        raise AppException(409, "Cannot delete quiz that already has student attempts.", "QUIZ_HAS_ATTEMPTS")

    # Delete questions (cascades to quiz_options)
    questions = list(db.scalars(select(Question).where(Question.quiz_id == quiz_id)).all())
    for q in questions:
        q.correct_option_id = None
    db.flush()
    for q in questions:
        db.delete(q)
    db.delete(quiz)
    db.commit()


def list_admin_questions(db: Session, quiz_id: int, current_user: User) -> list[dict]:
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise AppException(404, "Quiz not found.", "QUIZ_NOT_FOUND")
    ensure_course_write_access(db, quiz.course_id, current_user)

    questions = list(
        db.scalars(
            select(Question)
            .where(Question.quiz_id == quiz_id)
            .order_by(asc(Question.sort_order), asc(Question.id))
        ).all()
    )
    result = []
    for q in questions:
        opts = list(
            db.scalars(
                select(QuizOption)
                .where(QuizOption.question_id == q.id)
                .order_by(asc(QuizOption.sort_order), asc(QuizOption.id))
            ).all()
        )
        result.append(
            {
                "id": q.id,
                "quiz_id": q.quiz_id,
                "question_text": q.question_text,
                "marks": q.marks,
                "sort_order": q.sort_order,
                "correct_option_id": q.correct_option_id,
                "options": opts,
            }
        )
    return result


def add_question(db: Session, quiz_id: int, payload: QuestionCreate, current_user: User) -> dict:
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise AppException(404, "Quiz not found.", "QUIZ_NOT_FOUND")
    ensure_course_write_access(db, quiz.course_id, current_user)

    question = Question(
        quiz_id=quiz.id,
        question_text=payload.question_text.strip(),
        marks=payload.marks,
        sort_order=payload.sort_order,
    )
    db.add(question)
    db.flush()

    created_opts: list[QuizOption] = []
    for idx, opt_text in enumerate(payload.options, start=1):
        opt = QuizOption(
            question_id=question.id,
            option_text=opt_text.strip(),
            sort_order=idx,
        )
        db.add(opt)
        db.flush()
        created_opts.append(opt)

    question.correct_option_id = created_opts[payload.correct_option_index].id

    # Keep quiz.total_marks synced with sum of question marks
    total_q_marks = db.scalar(
        select(func.coalesce(func.sum(Question.marks), 0)).where(Question.quiz_id == quiz.id)
    )
    quiz.total_marks = Decimal(str(total_q_marks))
    db.commit()
    db.refresh(question)
    return {
        "id": question.id,
        "quiz_id": question.quiz_id,
        "question_text": question.question_text,
        "marks": question.marks,
        "sort_order": question.sort_order,
        "correct_option_id": question.correct_option_id,
        "options": created_opts,
    }


def update_question(
    db: Session, quiz_id: int, question_id: int, payload: QuestionUpdate, current_user: User
) -> dict:
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise AppException(404, "Quiz not found.", "QUIZ_NOT_FOUND")
    ensure_course_write_access(db, quiz.course_id, current_user)

    question = db.scalar(
        select(Question).where(Question.id == question_id, Question.quiz_id == quiz_id)
    )
    if not question:
        raise AppException(404, "Question not found.", "QUESTION_NOT_FOUND")

    if payload.question_text is not None:
        question.question_text = payload.question_text.strip()
    if payload.marks is not None:
        question.marks = payload.marks
    if payload.sort_order is not None:
        question.sort_order = payload.sort_order

    if payload.options is not None:
        question.correct_option_id = None
        db.flush()
        old_opts = list(db.scalars(select(QuizOption).where(QuizOption.question_id == question.id)).all())
        for o in old_opts:
            db.delete(o)
        db.flush()

        new_opts: list[QuizOption] = []
        for idx, opt_text in enumerate(payload.options, start=1):
            opt = QuizOption(question_id=question.id, option_text=opt_text.strip(), sort_order=idx)
            db.add(opt)
            db.flush()
            new_opts.append(opt)

        c_idx = payload.correct_option_index if payload.correct_option_index is not None else 0
        if c_idx >= len(new_opts):
            raise AppException(422, "correct_option_index out of range.", "INVALID_OPTION_INDEX")
        question.correct_option_id = new_opts[c_idx].id

    total_q_marks = db.scalar(
        select(func.coalesce(func.sum(Question.marks), 0)).where(Question.quiz_id == quiz.id)
    )
    quiz.total_marks = Decimal(str(total_q_marks))
    db.commit()

    opts = list(
        db.scalars(
            select(QuizOption).where(QuizOption.question_id == question.id).order_by(QuizOption.sort_order.asc())
        ).all()
    )
    return {
        "id": question.id,
        "quiz_id": question.quiz_id,
        "question_text": question.question_text,
        "marks": question.marks,
        "sort_order": question.sort_order,
        "correct_option_id": question.correct_option_id,
        "options": opts,
    }


def delete_question(db: Session, quiz_id: int, question_id: int, current_user: User) -> None:
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise AppException(404, "Quiz not found.", "QUIZ_NOT_FOUND")
    ensure_course_write_access(db, quiz.course_id, current_user)

    has_attempts = db.scalar(select(QuizAttempt.id).where(QuizAttempt.quiz_id == quiz_id)) is not None
    if has_attempts:
        raise AppException(409, "Cannot delete questions after attempts exist.", "QUIZ_HAS_ATTEMPTS")

    question = db.scalar(
        select(Question).where(Question.id == question_id, Question.quiz_id == quiz_id)
    )
    if not question:
        raise AppException(404, "Question not found.", "QUESTION_NOT_FOUND")

    question.correct_option_id = None
    db.flush()
    db.delete(question)
    db.flush()

    total_q_marks = db.scalar(
        select(func.coalesce(func.sum(Question.marks), 0)).where(Question.quiz_id == quiz.id)
    )
    quiz.total_marks = Decimal(str(total_q_marks))
    db.commit()


def _attempt_deadline(attempt: QuizAttempt, quiz: Quiz, *, include_grace: bool = False) -> datetime:
    extra = TIMER_GRACE_SECONDS if include_grace else 0
    return _to_utc(attempt.started_at) + timedelta(minutes=quiz.time_limit_minutes, seconds=extra)


def _finalise_attempt(db: Session, attempt: QuizAttempt, quiz: Quiz, *, at_time: datetime | None = None) -> QuizAttempt:
    """Compute score server-side from saved QuizAnswer rows and finalise the attempt."""
    if attempt.submitted_at is not None:
        return attempt

    questions = list(db.scalars(select(Question).where(Question.quiz_id == quiz.id)).all())
    answers = list(db.scalars(select(QuizAnswer).where(QuizAnswer.attempt_id == attempt.id)).all())
    ans_by_qid = {a.question_id: a for a in answers}

    score = Decimal("0.00")
    for q in questions:
        ans = ans_by_qid.get(q.id)
        if ans and ans.selected_option_id is not None and ans.selected_option_id == q.correct_option_id:
            ans.is_correct = True
            score += q.marks
        elif ans:
            ans.is_correct = False

    attempt.score = score
    attempt.is_passed = score >= quiz.passing_marks
    attempt.submitted_at = at_time or datetime.now(timezone.utc)
    db.commit()
    db.refresh(attempt)
    return attempt


def _auto_finalise_if_expired(db: Session, attempt: QuizAttempt, quiz: Quiz) -> bool:
    """If an unsubmitted attempt is past deadline (+ grace), auto-finalise it and return True."""
    if attempt.submitted_at is not None:
        return False
    now = datetime.now(timezone.utc)
    grace_deadline = _attempt_deadline(attempt, quiz, include_grace=True)
    if now > grace_deadline:
        _finalise_attempt(db, attempt, quiz, at_time=_attempt_deadline(attempt, quiz, include_grace=False))
        return True
    return False


def _build_active_attempt_payload(db: Session, attempt: QuizAttempt, quiz: Quiz) -> dict:
    now = datetime.now(timezone.utc)
    expires_at = _attempt_deadline(attempt, quiz, include_grace=False)
    remaining = max(0, int((expires_at - now).total_seconds()))

    questions = list(
        db.scalars(
            select(Question)
            .where(Question.quiz_id == quiz.id)
            .order_by(asc(Question.sort_order), asc(Question.id))
        ).all()
    )
    answers = list(db.scalars(select(QuizAnswer).where(QuizAnswer.attempt_id == attempt.id)).all())
    selected_map = {a.question_id: a.selected_option_id for a in answers}

    q_payload = []
    for q in questions:
        opts = list(
            db.scalars(
                select(QuizOption)
                .where(QuizOption.question_id == q.id)
                .order_by(asc(QuizOption.sort_order), asc(QuizOption.id))
            ).all()
        )
        # IMPORTANT: Do NOT include correct_option_id in active attempt payload!
        q_payload.append(
            {
                "id": q.id,
                "quiz_id": q.quiz_id,
                "question_text": q.question_text,
                "marks": q.marks,
                "sort_order": q.sort_order,
                "options": opts,
                "selected_option_id": selected_map.get(q.id),
            }
        )

    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz.id,
        "quiz_title": quiz.title,
        "attempt_number": attempt.attempt_number,
        "started_at": attempt.started_at,
        "expires_at": expires_at,
        "remaining_seconds": remaining,
        "is_submitted": False,
        "questions": q_payload,
    }


def _build_result_payload(db: Session, attempt: QuizAttempt, quiz: Quiz) -> dict:
    student = db.scalar(select(User).where(User.id == attempt.student_id))
    questions = list(
        db.scalars(
            select(Question)
            .where(Question.quiz_id == quiz.id)
            .order_by(asc(Question.sort_order), asc(Question.id))
        ).all()
    )
    answers = list(db.scalars(select(QuizAnswer).where(QuizAnswer.attempt_id == attempt.id)).all())
    ans_map = {a.question_id: a for a in answers}

    review_questions = []
    for q in questions:
        opts = list(
            db.scalars(
                select(QuizOption)
                .where(QuizOption.question_id == q.id)
                .order_by(asc(QuizOption.sort_order), asc(QuizOption.id))
            ).all()
        )
        ans = ans_map.get(q.id)
        review_questions.append(
            {
                "id": q.id,
                "question_text": q.question_text,
                "marks": q.marks,
                "sort_order": q.sort_order,
                "options": opts,
                "selected_option_id": ans.selected_option_id if ans else None,
                "correct_option_id": q.correct_option_id,
                "is_correct": ans.is_correct if ans else False,
            }
        )

    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz.id,
        "quiz_title": quiz.title,
        "student_id": attempt.student_id,
        "student_name": student.full_name if student else None,
        "attempt_number": attempt.attempt_number,
        "started_at": attempt.started_at,
        "submitted_at": attempt.submitted_at,
        "score": attempt.score,
        "total_marks": quiz.total_marks,
        "passing_marks": quiz.passing_marks,
        "is_passed": attempt.is_passed,
        "is_submitted": True,
        "questions": review_questions,
    }


def start_quiz_attempt(db: Session, quiz_id: int, current_user: User) -> dict:
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise AppException(404, "Quiz not found.", "QUIZ_NOT_FOUND")

    _ensure_student_quiz_access(db, quiz, current_user.id)

    now = datetime.now(timezone.utc)
    if quiz.available_from is not None and now < _to_utc(quiz.available_from):
        raise AppException(400, "Quiz has not opened yet.", "QUIZ_OUTSIDE_WINDOW")
    if quiz.available_until is not None and now > _to_utc(quiz.available_until):
        raise AppException(400, "Quiz availability window has closed.", "QUIZ_OUTSIDE_WINDOW")

    attempts = list(
        db.scalars(
            select(QuizAttempt)
            .where(QuizAttempt.quiz_id == quiz.id, QuizAttempt.student_id == current_user.id)
            .order_by(QuizAttempt.attempt_number.asc())
        ).all()
    )

    # Auto-finalise any expired in-progress attempts
    for att in attempts:
        _auto_finalise_if_expired(db, att, quiz)

    # Resume active attempt if one is still open
    for att in attempts:
        if att.submitted_at is None:
            return _build_active_attempt_payload(db, att, quiz)

    if not quiz.allow_retake and len(attempts) >= 1:
        raise AppException(409, "You have already attempted this quiz.", "DUPLICATE_ATTEMPT")
    if quiz.allow_retake and len(attempts) >= quiz.max_attempts:
        raise AppException(409, "Maximum quiz attempts reached.", "MAX_ATTEMPTS_REACHED")

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=current_user.id,
        attempt_number=len(attempts) + 1,
        started_at=now,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return _build_active_attempt_payload(db, attempt, quiz)


def get_attempt(db: Session, attempt_id: int, current_user: User) -> dict:
    attempt = db.scalar(select(QuizAttempt).where(QuizAttempt.id == attempt_id))
    if not attempt:
        raise AppException(404, "Quiz attempt not found.", "ATTEMPT_NOT_FOUND")

    quiz = db.scalar(select(Quiz).where(Quiz.id == attempt.quiz_id))
    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Student":
        if attempt.student_id != current_user.id:
            raise AppException(403, "You can only view your own quiz attempts.", "FORBIDDEN")
    else:
        ensure_course_read_access(db, quiz.course_id, current_user)

    _auto_finalise_if_expired(db, attempt, quiz)

    if attempt.submitted_at is not None:
        return _build_result_payload(db, attempt, quiz)
    return _build_active_attempt_payload(db, attempt, quiz)


def save_attempt_answer(
    db: Session, attempt_id: int, question_id: int, selected_option_id: int, current_user: User
) -> dict:
    attempt = db.scalar(select(QuizAttempt).where(QuizAttempt.id == attempt_id))
    if not attempt:
        raise AppException(404, "Quiz attempt not found.", "ATTEMPT_NOT_FOUND")
    if attempt.student_id != current_user.id:
        raise AppException(403, "You can only answer your own quiz attempt.", "FORBIDDEN")

    quiz = db.scalar(select(Quiz).where(Quiz.id == attempt.quiz_id))
    if _auto_finalise_if_expired(db, attempt, quiz):
        raise AppException(
            400,
            "Quiz time has expired; your attempt was automatically submitted.",
            "QUIZ_TIME_EXPIRED",
        )
    if attempt.submitted_at is not None:
        raise AppException(409, "Quiz attempt has already been submitted.", "ALREADY_SUBMITTED")

    question = db.scalar(
        select(Question).where(Question.id == question_id, Question.quiz_id == quiz.id)
    )
    if not question:
        raise AppException(404, "Question not found in this quiz.", "QUESTION_NOT_FOUND")

    option = db.scalar(
        select(QuizOption).where(
            QuizOption.id == selected_option_id,
            QuizOption.question_id == question.id,
        )
    )
    if not option:
        raise AppException(400, "Selected option does not belong to this question.", "INVALID_OPTION")

    existing = db.scalar(
        select(QuizAnswer).where(
            QuizAnswer.attempt_id == attempt.id,
            QuizAnswer.question_id == question.id,
        )
    )
    if existing:
        existing.selected_option_id = option.id
    else:
        db.add(
            QuizAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option_id=option.id,
                is_correct=False,
            )
        )
    db.commit()
    return {"detail": "Answer saved."}


def submit_attempt(db: Session, attempt_id: int, current_user: User) -> dict:
    attempt = db.scalar(select(QuizAttempt).where(QuizAttempt.id == attempt_id))
    if not attempt:
        raise AppException(404, "Quiz attempt not found.", "ATTEMPT_NOT_FOUND")
    if attempt.student_id != current_user.id:
        raise AppException(403, "You can only submit your own quiz attempt.", "FORBIDDEN")

    quiz = db.scalar(select(Quiz).where(Quiz.id == attempt.quiz_id))
    if attempt.submitted_at is None:
        now = datetime.now(timezone.utc)
        grace_deadline = _attempt_deadline(attempt, quiz, include_grace=True)
        final_time = _attempt_deadline(attempt, quiz, include_grace=False) if now > grace_deadline else now
        _finalise_attempt(db, attempt, quiz, at_time=final_time)

    return _build_result_payload(db, attempt, quiz)


def list_quiz_results(db: Session, quiz_id: int, current_user: User) -> list[dict]:
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise AppException(404, "Quiz not found.", "QUIZ_NOT_FOUND")
    ensure_course_write_access(db, quiz.course_id, current_user)

    rows = db.execute(
        select(QuizAttempt, User)
        .join(User, User.id == QuizAttempt.student_id)
        .where(QuizAttempt.quiz_id == quiz.id)
        .order_by(QuizAttempt.started_at.desc())
    ).all()

    results = []
    for att, user in rows:
        _auto_finalise_if_expired(db, att, quiz)
        results.append(
            {
                "attempt_id": att.id,
                "student_id": user.id,
                "student_name": user.full_name,
                "student_email": user.email,
                "attempt_number": att.attempt_number,
                "started_at": att.started_at,
                "submitted_at": att.submitted_at,
                "score": att.score,
                "is_passed": att.is_passed,
            }
        )
    return results
