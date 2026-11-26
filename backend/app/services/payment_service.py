from datetime import datetime, timezone
from decimal import Decimal
import secrets
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.middleware.error_handler import AppException
from app.models import Course, Enrollment, Payment, PaymentStatus, Role, User
from app.schemas.payment import (
    CourseFeeReportItem,
    PaginatedPaymentsResponse,
    PaymentCreateRequest,
    PaymentRefundRequest,
    PaymentResponse,
    StudentCourseFeeSummary,
    StudentFeeReportItem,
    StudentPaymentsMeResponse,
)
from app.utils.pdf_generator import generate_receipt_pdf


def generate_receipt_number() -> str:
    year = datetime.now(timezone.utc).year
    suffix = secrets.token_hex(4).upper()
    return f"RCP-{year}-{suffix}"


def get_student_course_fee_summary(db: Session, student_id: int, course_id: int) -> dict:
    course = db.get(Course, course_id)
    if not course:
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")

    fee_amount = float(course.fee_amount)

    # Sum only successful non-refunded payments
    paid_stmt = select(func.coalesce(func.sum(Payment.amount_paid), Decimal("0.00"))).where(
        Payment.student_id == student_id,
        Payment.course_id == course_id,
        Payment.status.in_([PaymentStatus.PAID, PaymentStatus.PARTIALLY_PAID]),
    )
    total_paid = float(db.scalar(paid_stmt) or 0.0)
    total_pending = max(0.0, fee_amount - total_paid)

    if total_paid >= fee_amount and fee_amount > 0:
        status_str = "Paid"
    elif total_paid > 0:
        status_str = "Partially Paid"
    else:
        # Check if there are refunded payments
        refund_stmt = select(func.count(Payment.id)).where(
            Payment.student_id == student_id,
            Payment.course_id == course_id,
            Payment.status == PaymentStatus.REFUNDED,
        )
        has_refund = (db.scalar(refund_stmt) or 0) > 0
        status_str = "Refunded" if has_refund else "Pending"

    return {
        "course_id": course.id,
        "course_title": course.title,
        "course_code": course.code,
        "total_fee": fee_amount,
        "total_paid": round(total_paid, 2),
        "total_pending": round(total_pending, 2),
        "status": status_str,
    }


def record_payment(db: Session, payload: PaymentCreateRequest, current_user: User) -> dict:
    """Record payment installment with overpayment protection and automated status derivation."""
    # 1. Validate student
    student = db.scalar(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(User.id == payload.student_id, Role.name == "Student")
    )
    if not student:
        raise AppException(404, "Student not found.", "STUDENT_NOT_FOUND")

    # 2. Validate course
    course = db.get(Course, payload.course_id)
    if not course:
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")

    total_fee = float(course.fee_amount)
    installment_amount = float(payload.amount)

    # 3. Transactional validation
    with db.begin_nested():
        # Query current paid sum for this student+course
        paid_stmt = select(func.coalesce(func.sum(Payment.amount_paid), Decimal("0.00"))).where(
            Payment.student_id == payload.student_id,
            Payment.course_id == payload.course_id,
            Payment.status.in_([PaymentStatus.PAID, PaymentStatus.PARTIALLY_PAID]),
        )
        currently_paid = float(db.scalar(paid_stmt) or 0.0)
        outstanding = max(0.0, total_fee - currently_paid)

        # Overpayment guard
        if round(installment_amount, 2) > round(outstanding, 2):
            raise AppException(
                400,
                f"Payment amount (${installment_amount:,.2f}) exceeds outstanding fee balance (${outstanding:,.2f}). Overpayment is rejected.",
                "OVERPAYMENT_REJECTED",
            )

        new_total_paid = currently_paid + installment_amount
        derived_status = (
            PaymentStatus.PAID if new_total_paid >= total_fee else PaymentStatus.PARTIALLY_PAID
        )

        receipt_no = generate_receipt_number()
        # Find enrollment
        enrollment_id = db.scalar(
            select(Enrollment.id).where(
                Enrollment.student_id == payload.student_id,
                Enrollment.course_id == payload.course_id,
            )
        )

        payment = Payment(
            student_id=payload.student_id,
            course_id=payload.course_id,
            enrollment_id=enrollment_id,
            amount_due=Decimal(str(total_fee)),
            amount_paid=payload.amount,
            payment_method=payload.payment_method,
            transaction_ref=payload.transaction_ref or receipt_no,
            receipt_number=receipt_no,
            status=derived_status,
            paid_at=payload.payment_date or datetime.now(timezone.utc),
            recorded_by=current_user.id,
            notes=payload.notes,
        )
        db.add(payment)
        db.flush()

    db.commit()
    db.refresh(payment)

    return _format_payment_response(payment, student=student, course=course, recorder=current_user)


def refund_payment(db: Session, payment_id: int, payload: PaymentRefundRequest, current_user: User) -> dict:
    """Refund an existing payment record, updating fee balances and audit log."""
    payment = db.get(Payment, payment_id)
    if not payment:
        raise AppException(404, "Payment record not found.", "PAYMENT_NOT_FOUND")

    if payment.status == PaymentStatus.REFUNDED:
        raise AppException(400, "This payment has already been refunded.", "ALREADY_REFUNDED")

    with db.begin_nested():
        payment.status = PaymentStatus.REFUNDED
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        refund_note = f"[REFUNDED on {now_str} by {current_user.full_name}: {payload.reason}]"
        payment.notes = f"{payment.notes}\n{refund_note}" if payment.notes else refund_note
        db.flush()

    db.commit()
    db.refresh(payment)

    student = db.get(User, payment.student_id)
    course = db.get(Course, payment.course_id)
    recorder = db.get(User, payment.recorded_by) if payment.recorded_by else None
    return _format_payment_response(payment, student=student, course=course, recorder=recorder)


def get_student_payments_me(db: Session, current_user: User) -> dict:
    """Return all payment transactions and fee summaries per course for current student."""
    # Find all courses the student has enrolled in or made payments for
    enrolled_courses = db.scalars(
        select(Enrollment.course_id).where(Enrollment.student_id == current_user.id)
    ).all()
    paid_courses = db.scalars(
        select(Payment.course_id).where(Payment.student_id == current_user.id)
    ).all()
    all_course_ids = sorted(list(set(enrolled_courses + paid_courses)))

    fee_summaries = [
        StudentCourseFeeSummary(**get_student_course_fee_summary(db, current_user.id, c_id))
        for c_id in all_course_ids
    ]

    payments = db.scalars(
        select(Payment)
        .where(Payment.student_id == current_user.id)
        .order_by(desc(Payment.created_at))
    ).all()

    formatted_payments = [
        PaymentResponse(**_format_payment_response(p, student=current_user))
        for p in payments
    ]

    return {
        "student_id": current_user.id,
        "fee_summaries": fee_summaries,
        "payments": formatted_payments,
    }


def list_payments(
    db: Session,
    *,
    student_id: int | None = None,
    course_id: int | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """List payment transactions with filtering and pagination for Admin."""
    stmt = select(Payment)
    if student_id:
        stmt = stmt.where(Payment.student_id == student_id)
    if course_id:
        stmt = stmt.where(Payment.course_id == course_id)
    if status_filter:
        stmt = stmt.where(Payment.status == status_filter)

    count_stmt = select(func.count(Payment.id)).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    # Total collected across all successful payments matching filter
    collected_stmt = select(func.coalesce(func.sum(Payment.amount_paid), Decimal("0.00"))).where(
        Payment.status.in_([PaymentStatus.PAID, PaymentStatus.PARTIALLY_PAID])
    )
    if student_id:
        collected_stmt = collected_stmt.where(Payment.student_id == student_id)
    if course_id:
        collected_stmt = collected_stmt.where(Payment.course_id == course_id)
    total_collected = float(db.scalar(collected_stmt) or 0.0)

    # Total pending estimation
    total_pending = 0.0
    if student_id and course_id:
        summ = get_student_course_fee_summary(db, student_id, course_id)
        total_pending = summ["total_pending"]

    stmt = stmt.order_by(desc(Payment.created_at)).offset((page - 1) * page_size).limit(page_size)
    items = db.scalars(stmt).all()

    total_pages = max(1, (total + page_size - 1) // page_size)
    formatted = [_format_payment_response(p) for p in items]

    return {
        "items": formatted,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_collected": round(total_collected, 2),
        "total_pending": round(total_pending, 2),
    }


def get_receipt_pdf(db: Session, payment_id: int, current_user: User) -> tuple[bytes, str]:
    """Verify authorization and generate dynamic PDF receipt."""
    payment = db.get(Payment, payment_id)
    if not payment:
        raise AppException(404, "Payment record not found.", "PAYMENT_NOT_FOUND")

    # Authorization
    is_admin = current_user.role and current_user.role.name == "Admin"
    if not is_admin and payment.student_id != current_user.id:
        raise AppException(403, "You can only download your own payment receipts.", "FORBIDDEN")

    student = db.get(User, payment.student_id)
    course = db.get(Course, payment.course_id)
    recorder = db.get(User, payment.recorded_by) if payment.recorded_by else None

    summary = get_student_course_fee_summary(db, payment.student_id, payment.course_id)

    pdf_bytes = generate_receipt_pdf(
        receipt_number=payment.receipt_number or f"RCP-{payment.id}",
        payment_id=payment.id,
        student_name=student.full_name if student else "Student",
        student_email=student.email if student else "",
        course_title=course.title if course else "Course",
        course_code=course.code if course else "",
        amount_paid=float(payment.amount_paid),
        total_fee=summary["total_fee"],
        total_paid_to_date=summary["total_paid"],
        pending_balance=summary["total_pending"],
        payment_status=payment.status.value if hasattr(payment.status, "value") else str(payment.status),
        payment_method=payment.payment_method or "Cash",
        transaction_ref=payment.transaction_ref,
        paid_at=payment.paid_at,
        recorded_by_name=recorder.full_name if recorder else "Finance Admin",
        notes=payment.notes,
    )
    filename = f"Receipt-{payment.receipt_number or payment.id}.pdf"
    return pdf_bytes, filename


def get_student_fee_report(db: Session) -> list[dict]:
    """Generate comprehensive student-wise fee balance report."""
    students = db.scalars(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(Role.name == "Student")
        .order_by(User.full_name)
    ).all()

    report = []
    for s in students:
        enrolled_courses = db.scalars(
            select(Course)
            .join(Enrollment, Enrollment.course_id == Course.id)
            .where(Enrollment.student_id == s.id)
        ).all()

        total_fees = sum(float(c.fee_amount) for c in enrolled_courses)
        paid_stmt = select(func.coalesce(func.sum(Payment.amount_paid), Decimal("0.00"))).where(
            Payment.student_id == s.id,
            Payment.status.in_([PaymentStatus.PAID, PaymentStatus.PARTIALLY_PAID]),
        )
        total_paid = float(db.scalar(paid_stmt) or 0.0)
        total_pending = max(0.0, total_fees - total_paid)

        if total_paid >= total_fees and total_fees > 0:
            status = "Paid"
        elif total_paid > 0:
            status = "Partially Paid"
        else:
            status = "Pending" if total_fees > 0 else "N/A"

        report.append(
            {
                "student_id": s.id,
                "student_name": s.full_name,
                "student_email": s.email,
                "courses_enrolled": len(enrolled_courses),
                "total_fees": round(total_fees, 2),
                "total_paid": round(total_paid, 2),
                "total_pending": round(total_pending, 2),
                "status": status,
            }
        )
    return report


def get_course_fee_report(db: Session) -> list[dict]:
    """Generate course-wise fee collection and revenue report."""
    courses = db.scalars(select(Course).order_by(Course.title)).all()

    report = []
    for c in courses:
        enrolled_count = db.scalar(
            select(func.count(Enrollment.id)).where(Enrollment.course_id == c.id)
        ) or 0
        fee_amount = float(c.fee_amount)
        expected_rev = fee_amount * enrolled_count

        collected_stmt = select(func.coalesce(func.sum(Payment.amount_paid), Decimal("0.00"))).where(
            Payment.course_id == c.id,
            Payment.status.in_([PaymentStatus.PAID, PaymentStatus.PARTIALLY_PAID]),
        )
        total_collected = float(db.scalar(collected_stmt) or 0.0)
        total_pending = max(0.0, expected_rev - total_collected)
        pct = (total_collected / expected_rev * 100.0) if expected_rev > 0 else 100.0

        report.append(
            {
                "course_id": c.id,
                "course_title": c.title,
                "course_code": c.code,
                "fee_amount": round(fee_amount, 2),
                "enrolled_students": enrolled_count,
                "total_expected_revenue": round(expected_rev, 2),
                "total_collected": round(total_collected, 2),
                "total_pending": round(total_pending, 2),
                "collection_percentage": round(pct, 1),
            }
        )
    return report


def _format_payment_response(
    payment: Payment,
    *,
    student: User | None = None,
    course: Course | None = None,
    recorder: User | None = None,
) -> dict:
    # Fallback to fetch related objects if not passed
    student_obj = student or getattr(payment, "student", None)
    course_obj = course or getattr(payment, "course", None)
    recorder_obj = recorder or getattr(payment, "recorder", None)

    return {
        "id": payment.id,
        "student_id": payment.student_id,
        "student_name": student_obj.full_name if student_obj else None,
        "student_email": student_obj.email if student_obj else None,
        "course_id": payment.course_id,
        "course_title": course_obj.title if course_obj else None,
        "course_code": course_obj.code if course_obj else None,
        "enrollment_id": payment.enrollment_id,
        "amount_due": float(payment.amount_due),
        "amount_paid": float(payment.amount_paid),
        "payment_method": payment.payment_method,
        "transaction_ref": payment.transaction_ref,
        "receipt_number": payment.receipt_number,
        "status": payment.status.value if hasattr(payment.status, "value") else str(payment.status),
        "paid_at": payment.paid_at,
        "recorded_by": payment.recorded_by,
        "recorded_by_name": recorder_obj.full_name if recorder_obj else None,
        "notes": payment.notes,
        "created_at": payment.created_at,
    }
