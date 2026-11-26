from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=1)
    phone: str | None = Field(default=None, max_length=30)
    is_active: bool = True


class StudentUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None


class StudentResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentEnrollmentSummary(BaseModel):
    enrollment_id: int
    course_id: int
    course_title: str
    course_code: str
    batch_id: int | None = None
    batch_name: str | None = None
    status: str
    enrolled_at: datetime


class StudentBatchSummary(BaseModel):
    batch_id: int
    batch_name: str
    batch_code: str
    course_title: str
    start_date: date
    end_date: date | None = None
    status: str


class StudentDetailResponse(StudentResponse):
    enrollments: list[StudentEnrollmentSummary] = []
    batches: list[StudentBatchSummary] = []
    attendance_percentage: float = 0.0
    progress_percentage: float = 0.0


class PaginatedStudentsResponse(BaseModel):
    items: list[StudentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
