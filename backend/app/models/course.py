import enum
from decimal import Decimal
from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Course(TimestampMixin, Base):
    """Course catalog item; soft-deleted via status='archived'."""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_weeks: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[CourseStatus] = mapped_column(
        Enum(CourseStatus, name="course_status_enum"),
        default=CourseStatus.DRAFT,
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting an instructor assigned as lead on a course.
    instructor_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("instructors.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    # RESTRICT: preserve course authorship audit trail; users are soft-deleted.
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    modules: Mapped[list["CourseModule"]] = relationship("CourseModule", back_populates="course")


class CourseModule(TimestampMixin, Base):
    """Structured module within a course."""

    __tablename__ = "course_modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a course that still has modules.
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="modules")
    lectures: Mapped[list["Lecture"]] = relationship("Lecture", back_populates="module")


class Lecture(TimestampMixin, Base):
    """Individual lecture belonging to a course module (and optionally a batch)."""

    __tablename__ = "lectures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a module that has lectures.
    module_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("course_modules.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting a batch that has scheduled lectures.
    batch_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # RESTRICT: preserve creator reference.
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    module: Mapped["CourseModule"] = relationship("CourseModule", back_populates="lectures")


class StudyMaterial(TimestampMixin, Base):
    """Metadata and URL for downloadable study materials (no binary storage)."""

    __tablename__ = "study_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a course with attached study materials.
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: prevent deleting a module with attached study materials.
    module_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("course_modules.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    # RESTRICT: prevent deleting a lecture with attached study materials.
    lecture_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("lectures.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # RESTRICT: preserve uploader reference.
    uploaded_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
