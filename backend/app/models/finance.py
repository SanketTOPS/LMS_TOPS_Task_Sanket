import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class PaymentStatus(str, enum.Enum):
    PAID = "Paid"
    PARTIALLY_PAID = "Partially Paid"
    PENDING = "Pending"
    FAILED = "Failed"
    REFUNDED = "Refunded"


class Payment(TimestampMixin, Base):
    """Fee payment record linked to student, course, and optional enrollment."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # RESTRICT: financial records must never be cascade-deleted.
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: preserve course fee payment history.
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT: preserve link to enrollment record.
    enrollment_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("enrollments.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    amount_due: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transaction_ref: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    receipt_number: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # RESTRICT: preserve audit trail of staff who recorded payment.
    recorded_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
