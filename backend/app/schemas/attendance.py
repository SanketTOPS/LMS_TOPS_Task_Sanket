from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AttendanceRecordInput(BaseModel):
    student_id: int
    status: Literal["Present", "Absent", "Approved Leave"]
    remarks: str | None = Field(default=None, max_length=255)


class AttendanceBulkRequest(BaseModel):
    batch_id: int
    class_date: date
    session_status: Literal["held", "cancelled", "holiday"] = "held"
    notes: str | None = Field(default=None, max_length=255)
    records: list[AttendanceRecordInput] = []


class AttendanceSingleCreate(BaseModel):
    student_id: int
    batch_id: int
    class_date: date
    status: Literal["Present", "Absent", "Approved Leave"] = "Present"
    remarks: str | None = Field(default=None, max_length=255)


class AttendanceRosterItem(BaseModel):
    student_id: int
    full_name: str
    email: str
    status: str | None = None
    remarks: str | None = None


class AttendanceRosterResponse(BaseModel):
    batch_id: int
    batch_name: str
    class_date: date
    session_status: str
    notes: str | None = None
    students: list[AttendanceRosterItem]


class AttendanceRecordResponse(BaseModel):
    id: int
    student_id: int
    batch_id: int
    batch_name: str | None = None
    class_date: date
    status: str
    remarks: str | None = None
    session_status: str = "held"
    marked_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MonthlyAttendanceSummary(BaseModel):
    month: str  # YYYY-MM
    present: int
    absent: int
    approved_leave: int
    eligible_classes: int
    percentage: float


class StudentAttendanceResponse(BaseModel):
    student_id: int
    total_present: int
    total_absent: int
    total_approved_leave: int
    total_eligible_classes: int
    attendance_percentage: float
    monthly_summary: list[MonthlyAttendanceSummary]
    records: list[AttendanceRecordResponse]
