from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreate(BaseModel):
    course_id: int
    batch_id: int | None = None
    module_id: int | None = None
    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    max_marks: Decimal = Field(default=Decimal("100.00"), gt=Decimal("0.00"))
    due_date: datetime
    allow_late: bool = False


class AssignmentUpdate(BaseModel):
    batch_id: int | None = None
    module_id: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    max_marks: Decimal | None = Field(default=None, gt=Decimal("0.00"))
    due_date: datetime | None = None
    allow_late: bool | None = None


class AssignmentFeedbackResponse(BaseModel):
    id: int
    submission_id: int
    instructor_id: int
    instructor_name: str | None = None
    comments: str
    marks_awarded: Decimal | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubmissionVersionResponse(BaseModel):
    id: int
    version_number: int
    submission_text: str | None = None
    file_name: str | None = None
    file_url: str | None = None
    file_size_bytes: int
    submitted_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    student_name: str | None = None
    student_email: str | None = None
    submission_text: str | None = None
    file_name: str | None = None
    file_url: str | None = None
    file_size_bytes: int
    submitted_at: datetime | None = None
    marks_obtained: Decimal | None = None
    status: str
    versions: list[SubmissionVersionResponse] = []
    feedback: list[AssignmentFeedbackResponse] = []

    model_config = ConfigDict(from_attributes=True)


class AssignmentResponse(BaseModel):
    id: int
    course_id: int
    course_title: str | None = None
    batch_id: int | None = None
    batch_name: str | None = None
    module_id: int | None = None
    title: str
    description: str | None = None
    attachment_name: str | None = None
    attachment_url: str | None = None
    max_marks: Decimal
    due_date: datetime
    allow_late: bool
    created_by: int
    created_at: datetime
    updated_at: datetime
    my_submission: SubmissionResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedAssignmentsResponse(BaseModel):
    items: list[AssignmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EvaluateSubmissionRequest(BaseModel):
    marks: Decimal = Field(..., ge=Decimal("0.00"))
    comments: str = Field(..., min_length=1)
