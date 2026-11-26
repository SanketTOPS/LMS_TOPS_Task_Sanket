from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CertificateGenerateRequest(BaseModel):
    course_id: int
    student_id: int | None = Field(
        default=None,
        description="Target student ID. If student invokes, defaults to current user.",
    )


class CertificateResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    student_email: str
    course_id: int
    course_title: str
    course_code: str
    batch_id: int | None = None
    batch_name: str | None = None
    certificate_number: str
    verification_code: str
    issued_at: datetime
    file_name: str | None = None
    file_url: str | None = None
    issued_by: int
    issued_by_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CertificateVerifyResponse(BaseModel):
    valid: bool
    certificate_number: str | None = None
    verification_code: str | None = None
    student_name: str | None = None
    course_title: str | None = None
    course_code: str | None = None
    issued_at: datetime | None = None
    message: str | None = None


class StudentCertificateEligibilityItem(BaseModel):
    course_id: int
    course_title: str
    course_code: str
    is_eligible: bool
    course_progress_percentage: float
    attendance_percentage: float
    all_quizzes_attempted: bool
    certificate: CertificateResponse | None = None
