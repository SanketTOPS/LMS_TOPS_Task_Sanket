from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudyMaterialResponse(BaseModel):
    id: int
    course_id: int
    module_id: int | None = None
    lecture_id: int | None = None
    title: str
    file_name: str
    file_url: str
    file_size_bytes: int
    mime_type: str | None = None
    uploaded_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LectureCreate(BaseModel):
    module_id: int
    batch_id: int | None = None
    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    video_url: str | None = Field(default=None, max_length=500)
    duration_minutes: int = Field(default=0, ge=0, le=1440)
    sort_order: int = Field(default=1, ge=1)
    is_published: bool = True


class LectureUpdate(BaseModel):
    module_id: int | None = None
    batch_id: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    video_url: str | None = Field(default=None, max_length=500)
    duration_minutes: int | None = Field(default=None, ge=0, le=1440)
    sort_order: int | None = Field(default=None, ge=1)
    is_published: bool | None = None


class LectureReorderRequest(BaseModel):
    module_id: int
    lecture_ids: list[int] = Field(..., min_length=1)


class LectureResponse(BaseModel):
    id: int
    module_id: int
    batch_id: int | None = None
    title: str
    description: str | None = None
    video_url: str | None = None
    duration_minutes: int
    sort_order: int
    is_published: bool
    created_by: int
    created_at: datetime
    updated_at: datetime
    materials: list[StudyMaterialResponse] = []
    is_completed: bool = False
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LectureProgressResponse(BaseModel):
    lecture_id: int
    student_id: int
    is_completed: bool
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CourseProgressResponse(BaseModel):
    course_id: int
    total_lectures: int
    completed_lectures: int
    progress_percentage: float
    completed_lecture_ids: list[int]
