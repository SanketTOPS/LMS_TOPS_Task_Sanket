import enum
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class BatchStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"


class Batch(TimestampMixin, Base):
    """Training cohort/batch for a course; soft-deleted via status='archived'."""

    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a course that has batches.
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting an instructor assigned to a batch.
    instructor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("instructors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    schedule_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_students: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status_enum"),
        default=BatchStatus.UPCOMING,
        nullable=False,
        index=True,
    )

    students: Mapped[list["BatchStudent"]] = relationship("BatchStudent", back_populates="batch")


class BatchStudent(TimestampMixin, Base):
    """Association between a batch and a student."""

    __tablename__ = "batch_students"
    __table_args__ = (
        UniqueConstraint("batch_id", "student_id", name="uq_batch_students_batch_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a batch that has assigned students.
    batch_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting a student user assigned to a batch.
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    batch: Mapped["Batch"] = relationship("Batch", back_populates="students")


class Enrollment(TimestampMixin, Base):
    """Course enrollment record preventing duplicate (student_id, course_id) pairs."""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_enrollments_student_course"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: preserve enrollment history; users are soft-deleted.
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting a course with enrollments.
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting a batch referenced by enrollments.
    batch_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus, name="enrollment_status_enum"),
        default=EnrollmentStatus.ACTIVE,
        nullable=False,
        index=True,
    )
