from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class Notification(TimestampMixin, Base):
    """User-targeted in-app notification."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: users are soft-deleted; retain notification audit records.
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    link_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Announcement(TimestampMixin, Base):
    """Institute-wide, course-level, or batch-level announcement."""

    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a course that has announcements.
    course_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    # RESTRICT: prevent deleting a batch that has announcements.
    batch_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # RESTRICT: preserve announcement author reference.
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
