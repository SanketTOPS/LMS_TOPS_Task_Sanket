from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class PaymentCreateRequest(BaseModel):
    student_id: int
    course_id: int
    amount: Decimal = Field(..., gt=0, description="Payment installment amount")
    payment_date: datetime | date | None = None
    payment_method: Literal["Cash", "Bank Transfer", "UPI", "Cheque", "Card", "Other"] = "Cash"
    transaction_ref: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=1000)


class PaymentRefundRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500, description="Mandatory refund explanation")


class PaymentResponse(BaseModel):
    id: int
    student_id: int
    student_name: str | None = None
    student_email: str | None = None
    course_id: int
    course_title: str | None = None
    course_code: str | None = None
    enrollment_id: int | None = None
    amount_due: float
    amount_paid: float
    payment_method: str | None = None
    transaction_ref: str | None = None
    receipt_number: str | None = None
    status: str
    paid_at: datetime | None = None
    recorded_by: int | None = None
    recorded_by_name: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentCourseFeeSummary(BaseModel):
    course_id: int
    course_title: str
    course_code: str
    total_fee: float
    total_paid: float
    total_pending: float
    status: str  # 'Paid', 'Partially Paid', 'Pending', 'Refunded'


class StudentPaymentsMeResponse(BaseModel):
    student_id: int
    fee_summaries: list[StudentCourseFeeSummary]
    payments: list[PaymentResponse]


class PaginatedPaymentsResponse(BaseModel):
    items: list[PaymentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    total_collected: float
    total_pending: float


class StudentFeeReportItem(BaseModel):
    student_id: int
    student_name: str
    student_email: str
    courses_enrolled: int
    total_fees: float
    total_paid: float
    total_pending: float
    status: str


class CourseFeeReportItem(BaseModel):
    course_id: int
    course_title: str
    course_code: str
    fee_amount: float
    enrolled_students: int
    total_expected_revenue: float
    total_collected: float
    total_pending: float
    collection_percentage: float
