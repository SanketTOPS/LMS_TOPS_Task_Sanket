import enum
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class AttendanceStatus(str, enum.Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    APPROVED_LEAVE = "Approved Leave"


class ClassSessionStatus(str, enum.Enum):
    HELD = "held"
    CANCELLED = "cancelled"
    HOLIDAY = "holiday"


class ClassSession(TimestampMixin, Base):
    """Tracks whether a scheduled batch date was held, cancelled, or a holiday."""

    __tablename__ = "class_sessions"
    __table_args__ = (
        UniqueConstraint("batch_id", "class_date", name="uq_class_sessions_batch_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a batch with session history.
    batch_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    class_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[ClassSessionStatus] = mapped_column(
        Enum(ClassSessionStatus, name="class_session_status_enum"),
        default=ClassSessionStatus.HELD,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # RESTRICT: preserve audit trail of who updated session status.
    updated_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )


class Attendance(TimestampMixin, Base):
    """Daily batch attendance per student; prevents duplicate entries per date."""

    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "batch_id", "class_date", name="uq_attendance_student_batch_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: preserve attendance history; users are soft-deleted.
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting a batch that has attendance records.
    batch_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    class_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, name="attendance_status_enum"),
        default=AttendanceStatus.PRESENT,
        nullable=False,
        index=True,
    )
    # RESTRICT: preserve audit trail of who marked attendance.
    marked_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)


class AttendanceAudit(Base):
    """Immutable audit log of attendance changes (who changed what and when)."""

    __tablename__ = "attendance_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: preserve audit trail for attendance records.
    attendance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("attendance.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    class_date: Mapped[date] = mapped_column(Date, nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    # RESTRICT: preserve audit trail of who made the change.
    changed_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)


class LectureProgress(TimestampMixin, Base):
    """Tracks student completion and watch time per lecture."""

    __tablename__ = "lecture_progress"
    __table_args__ = (
        UniqueConstraint("student_id", "lecture_id", name="uq_lecture_progress_student_lecture"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: preserve student progress records.
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting a lecture with student progress records.
    lecture_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lectures.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    watched_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Certificate(TimestampMixin, Base):
    """Issued completion certificate (metadata + file URL only)."""

    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_certificates_student_course"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: preserve issued certificate records.
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting a course with issued certificates.
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting a batch referenced by certificates.
    batch_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    certificate_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    verification_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # RESTRICT: preserve issuer audit trail.
    issued_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
