from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.payment import (
    CourseFeeReportItem,
    PaginatedPaymentsResponse,
    PaymentCreateRequest,
    PaymentRefundRequest,
    PaymentResponse,
    StudentFeeReportItem,
    StudentPaymentsMeResponse,
)
from app.services import payment_service

router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def record_payment(
    payload: PaymentCreateRequest,
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    """Admin: record manual payment installment with overpayment protection."""
    return PaymentResponse(**payment_service.record_payment(db, payload, current_user))


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(
    payment_id: int,
    payload: PaymentRefundRequest,
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    """Admin: refund payment installment with required explanation."""
    return PaymentResponse(**payment_service.refund_payment(db, payment_id, payload, current_user))


@router.get("", response_model=PaginatedPaymentsResponse)
def list_payments(
    student_id: int | None = Query(default=None),
    course_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> PaginatedPaymentsResponse:
    """Admin: list all payments with pagination, filters, and collection totals."""
    return PaginatedPaymentsResponse(
        **payment_service.list_payments(
            db,
            student_id=student_id,
            course_id=course_id,
            status_filter=status,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/me", response_model=StudentPaymentsMeResponse)
def get_my_payments(
    current_user: User = Depends(require_role(["Student"])),
    db: Session = Depends(get_db),
) -> StudentPaymentsMeResponse:
    """Student: view own payments and course fee balances only."""
    return StudentPaymentsMeResponse(
        **payment_service.get_student_payments_me(db, current_user)
    )


@router.get("/reports/student-wise", response_model=list[StudentFeeReportItem])
def get_student_fee_report(
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> list[StudentFeeReportItem]:
    """Admin: view aggregate fee collection and pending balances by student."""
    return [
        StudentFeeReportItem(**item) for item in payment_service.get_student_fee_report(db)
    ]


@router.get("/reports/course-wise", response_model=list[CourseFeeReportItem])
def get_course_fee_report(
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> list[CourseFeeReportItem]:
    """Admin: view aggregate revenue, fee collection, and pending balances by course."""
    return [
        CourseFeeReportItem(**item) for item in payment_service.get_course_fee_report(db)
    ]


@router.get("/{payment_id}/receipt")
def download_receipt(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download official PDF payment receipt (Student own or Admin)."""
    pdf_bytes, filename = payment_service.get_receipt_pdf(db, payment_id, current_user)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
