import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class SubmissionStatus(str, enum.Enum):
    PENDING = "Pending"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    EVALUATED = "Evaluated"
    LATE_SUBMISSION = "Late Submission"


class Assignment(TimestampMixin, Base):
    """Course/batch assignment with metadata-only attachment URL."""

    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a course that has assignments.
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting a batch that has assignments.
    batch_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    # RESTRICT: prevent deleting a module that has assignments.
    module_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("course_modules.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attachment_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("100.00"), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    allow_late: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # RESTRICT: preserve assignment creator audit trail.
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )


class Submission(TimestampMixin, Base):
    """Student submission for an assignment (metadata + file URL only)."""

    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_submissions_assignment_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting an assignment with student submissions.
    assignment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assignments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: preserve student submission records.
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    submission_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    marks_obtained: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status_enum"),
        default=SubmissionStatus.PENDING,
        nullable=False,
        index=True,
    )


class AssignmentFeedback(TimestampMixin, Base):
    """Instructor feedback and grading notes for a submission."""

    __tablename__ = "assignment_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a submission that has feedback history.
    submission_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("submissions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: preserve evaluator audit trail.
    instructor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    comments: Mapped[str] = mapped_column(Text, nullable=False)
    marks_awarded: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)


class SubmissionVersion(TimestampMixin, Base):
    """Version history for student assignment resubmissions."""

    __tablename__ = "submission_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # CASCADE: version rows are child history owned by the submission.
    submission_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    submission_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_version_status_enum"),
        nullable=False,
    )


class Quiz(TimestampMixin, Base):
    """MCQ quiz definition with retake policy."""

    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a course that has quizzes.
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting a batch that has quizzes.
    batch_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    passing_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0.00"), nullable=False)
    total_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0.00"), nullable=False)
    allow_retake: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    available_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    # RESTRICT: preserve quiz author reference.
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )


class Question(TimestampMixin, Base):
    """Quiz question; stores correct_option_id separately from quiz_options."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a quiz that still has questions.
    quiz_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quizzes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("1.00"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # SET NULL: breaks circular FK with quiz_options if an option is removed; stored separately on question.
    correct_option_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "quiz_options.id",
            name="fk_questions_correct_option_id",
            ondelete="SET NULL",
            use_alter=True,
        ),
        nullable=True,
    )

    options: Mapped[list["QuizOption"]] = relationship(
        "QuizOption",
        back_populates="question",
        foreign_keys="QuizOption.question_id",
        cascade="all, delete-orphan",
    )


class QuizOption(TimestampMixin, Base):
    """Answer option for a quiz question (child row; cascades on question delete)."""

    __tablename__ = "quiz_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # CASCADE: quiz_options are child rows owned by a question.
    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_text: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="options",
        foreign_keys=[question_id],
    )


class QuizAttempt(TimestampMixin, Base):
    """Student attempt on a quiz; unique per (quiz_id, student_id, attempt_number)."""

    __tablename__ = "quiz_attempts"
    __table_args__ = (
        UniqueConstraint(
            "quiz_id",
            "student_id",
            "attempt_number",
            name="uq_quiz_attempts_quiz_student_attempt",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a quiz with student attempts.
    quiz_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quizzes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: preserve student attempt history.
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0.00"), nullable=False)
    is_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    answers: Mapped[list["QuizAnswer"]] = relationship(
        "QuizAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )


class QuizAnswer(TimestampMixin, Base):
    """Individual question response inside a quiz attempt (child row; cascades)."""

    __tablename__ = "quiz_answers"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_quiz_answers_attempt_question"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # CASCADE: quiz_answers are child rows of a quiz_attempt.
    attempt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # CASCADE: remove answer child rows if a question is deleted.
    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # CASCADE: remove answer selection if an option is deleted.
    selected_option_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("quiz_options.id", ondelete="CASCADE"),
        nullable=True,
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    attempt: Mapped["QuizAttempt"] = relationship("QuizAttempt", back_populates="answers")
