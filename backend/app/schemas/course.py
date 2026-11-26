from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CourseModuleCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    sort_order: int = Field(default=1, ge=1)


class CourseModuleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    sort_order: int | None = Field(default=None, ge=1)


class CourseModuleResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: str | None = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=2, max_length=50)
    category: str | None = Field(default=None, max_length=100)
    description: str | None = None
    duration_weeks: int = Field(default=4, ge=1, le=260)
    fee_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    thumbnail_url: str | None = Field(default=None, max_length=500)
    instructor_id: int | None = None
    status: Literal["draft", "published", "archived"] = "draft"


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    code: str | None = Field(default=None, min_length=2, max_length=50)
    category: str | None = Field(default=None, max_length=100)
    description: str | None = None
    duration_weeks: int | None = Field(default=None, ge=1, le=260)
    fee_amount: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    thumbnail_url: str | None = Field(default=None, max_length=500)
    instructor_id: int | None = None


class CourseResponse(BaseModel):
    id: int
    title: str
    code: str
    category: str | None = None
    description: str | None = None
    duration_weeks: int
    fee_amount: Decimal
    thumbnail_url: str | None = None
    status: str
    instructor_id: int | None = None
    instructor_name: str | None = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseDetailResponse(CourseResponse):
    modules: list[CourseModuleResponse] = []
    enrollment_count: int = 0
    is_enrolled: bool = False


class PaginatedCoursesResponse(BaseModel):
    items: list[CourseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
