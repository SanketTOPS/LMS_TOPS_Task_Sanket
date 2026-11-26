from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class Role(TimestampMixin, Base):
    """System roles (Admin, Instructor, Student)."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="role")


class User(TimestampMixin, Base):
    """Application user account with soft-delete via is_active."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: prevent deleting a role that still has assigned users.
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Soft delete flag: deactivate instead of hard-deleting users.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    instructor_profile: Mapped["Instructor | None"] = relationship(
        "Instructor", back_populates="user", uselist=False
    )


class Instructor(TimestampMixin, Base):
    """Extended profile for users with the Instructor role."""

    __tablename__ = "instructors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: user accounts are soft-deleted; preserve instructor profile linkage.
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    expertise: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    user: Mapped["User"] = relationship("User", back_populates="instructor_profile")
