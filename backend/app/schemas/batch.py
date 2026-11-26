from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BatchCreate(BaseModel):
    course_id: int
    instructor_id: int
    name: str = Field(..., min_length=2, max_length=150)
    code: str = Field(..., min_length=2, max_length=50)
    start_date: date
    end_date: date | None = None
    schedule_info: str | None = Field(default=None, max_length=255)
    max_students: int = Field(default=30, ge=1, le=500)
    status: Literal["upcoming", "active", "closed", "archived"] = "upcoming"

    @model_validator(mode="after")
    def validate_dates(self) -> "BatchCreate":
        if self.end_date is not None and self.end_date <= self.start_date:
            raise ValueError("end_date must be strictly after start_date.")
        return self


class BatchUpdate(BaseModel):
    course_id: int | None = None
    instructor_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=150)
    code: str | None = Field(default=None, min_length=2, max_length=50)
    start_date: date | None = None
    end_date: date | None = None
    schedule_info: str | None = Field(default=None, max_length=255)
    max_students: int | None = Field(default=None, ge=1, le=500)

    @model_validator(mode="after")
    def validate_dates(self) -> "BatchUpdate":
        if self.start_date is not None and self.end_date is not None:
            if self.end_date <= self.start_date:
                raise ValueError("end_date must be strictly after start_date.")
        return self


class BatchResponse(BaseModel):
    id: int
    course_id: int
    course_title: str | None = None
    instructor_id: int
    instructor_name: str | None = None
    name: str
    code: str
    start_date: date
    end_date: date | None = None
    schedule_info: str | None = None
    max_students: int
    enrolled_count: int = 0
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedBatchesResponse(BaseModel):
    items: list[BatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BatchEnrollRequest(BaseModel):
    student_id: int


class BatchRosterStudent(BaseModel):
    student_id: int
    full_name: str
    email: str
    phone: str | None = None
    joined_at: datetime
    is_active: bool


class BatchRosterResponse(BaseModel):
    batch_id: int
    batch_name: str
    max_students: int
    enrolled_count: int
    students: list[BatchRosterStudent]
