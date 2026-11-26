from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InstructorCreate(BaseModel):
    user_id: int | None = None
    # Optional fields to create a new Instructor user + profile in one step
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    password: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    bio: str | None = None
    expertise: str | None = Field(default=None, max_length=255)
    qualification: str | None = Field(default=None, max_length=255)
    experience_years: int = Field(default=0, ge=0, le=70)


class InstructorUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    bio: str | None = None
    expertise: str | None = Field(default=None, max_length=255)
    qualification: str | None = Field(default=None, max_length=255)
    experience_years: int | None = Field(default=None, ge=0, le=70)
    is_active: bool | None = None


class InstructorResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: EmailStr
    phone: str | None = None
    bio: str | None = None
    expertise: str | None = None
    qualification: str | None = None
    experience_years: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedInstructorsResponse(BaseModel):
    items: list[InstructorResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class InstructorAssignRequest(BaseModel):
    course_id: int | None = None
    batch_id: int | None = None


class InstructorBatchSummary(BaseModel):
    batch_id: int
    batch_name: str
    batch_code: str
    course_id: int
    course_title: str
    start_date: date
    end_date: date | None = None
    status: str
