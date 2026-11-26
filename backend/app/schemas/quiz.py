from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuizOptionOut(BaseModel):
    id: int
    option_text: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=2)
    marks: Decimal = Field(default=Decimal("1.00"), gt=Decimal("0.00"))
    sort_order: int = Field(default=1, ge=1)
    options: list[str] = Field(..., min_length=2, max_length=6)
    correct_option_index: int = Field(..., ge=0)

    @model_validator(mode="after")
    def validate_correct_index(self) -> "QuestionCreate":
        if self.correct_option_index >= len(self.options):
            raise ValueError("correct_option_index must be a valid index into options.")
        return self


class QuestionUpdate(BaseModel):
    question_text: str | None = Field(default=None, min_length=2)
    marks: Decimal | None = Field(default=None, gt=Decimal("0.00"))
    sort_order: int | None = Field(default=None, ge=1)
    options: list[str] | None = Field(default=None, min_length=2, max_length=6)
    correct_option_index: int | None = Field(default=None, ge=0)


class QuestionAdminResponse(BaseModel):
    id: int
    quiz_id: int
    question_text: str
    marks: Decimal
    sort_order: int
    correct_option_id: int | None = None
    options: list[QuizOptionOut] = []

    model_config = ConfigDict(from_attributes=True)


class QuestionStudentResponse(BaseModel):
    """Question payload for active student attempts: NEVER includes correct_option_id."""

    id: int
    quiz_id: int
    question_text: str
    marks: Decimal
    sort_order: int
    options: list[QuizOptionOut] = []
    selected_option_id: int | None = None


class QuestionReviewResponse(BaseModel):
    """Question payload after submission: includes correct_option_id and correctness."""

    id: int
    question_text: str
    marks: Decimal
    sort_order: int
    options: list[QuizOptionOut] = []
    selected_option_id: int | None = None
    correct_option_id: int | None = None
    is_correct: bool = False


class QuizCreate(BaseModel):
    course_id: int
    batch_id: int | None = None
    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    time_limit_minutes: int = Field(default=30, ge=1, le=300)
    passing_marks: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    total_marks: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    allow_retake: bool = False
    max_attempts: int = Field(default=1, ge=1, le=20)
    available_from: datetime | None = None
    available_until: datetime | None = None
    is_published: bool = False

    @model_validator(mode="after")
    def validate_window(self) -> "QuizCreate":
        if (
            self.available_from is not None
            and self.available_until is not None
            and self.available_until <= self.available_from
        ):
            raise ValueError("available_until must be strictly after available_from.")
        return self


class QuizUpdate(BaseModel):
    batch_id: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    time_limit_minutes: int | None = Field(default=None, ge=1, le=300)
    passing_marks: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    total_marks: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    allow_retake: bool | None = None
    max_attempts: int | None = Field(default=None, ge=1, le=20)
    available_from: datetime | None = None
    available_until: datetime | None = None
    is_published: bool | None = None


class QuizResponse(BaseModel):
    id: int
    course_id: int
    course_title: str | None = None
    batch_id: int | None = None
    batch_name: str | None = None
    title: str
    description: str | None = None
    time_limit_minutes: int
    passing_marks: Decimal
    total_marks: Decimal
    allow_retake: bool
    max_attempts: int
    available_from: datetime | None = None
    available_until: datetime | None = None
    is_published: bool
    question_count: int = 0
    created_by: int
    created_at: datetime
    updated_at: datetime
    my_attempts_count: int = 0
    latest_attempt_id: int | None = None
    latest_attempt_submitted: bool = False

    model_config = ConfigDict(from_attributes=True)


class PaginatedQuizzesResponse(BaseModel):
    items: list[QuizResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SaveAnswerRequest(BaseModel):
    question_id: int
    selected_option_id: int


class AttemptActiveResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    attempt_number: int
    started_at: datetime
    expires_at: datetime
    remaining_seconds: int
    is_submitted: bool = False
    questions: list[QuestionStudentResponse]


class AttemptResultResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    student_id: int
    student_name: str | None = None
    attempt_number: int
    started_at: datetime
    submitted_at: datetime
    score: Decimal
    total_marks: Decimal
    passing_marks: Decimal
    is_passed: bool
    is_submitted: bool = True
    questions: list[QuestionReviewResponse] = []


class QuizResultRow(BaseModel):
    attempt_id: int
    student_id: int
    student_name: str
    student_email: str
    attempt_number: int
    started_at: datetime
    submitted_at: datetime | None = None
    score: Decimal
    is_passed: bool
