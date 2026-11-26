from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.attendance import (
    AttendanceBulkRequest,
    AttendanceRecordResponse,
    AttendanceRosterResponse,
    AttendanceSingleCreate,
    StudentAttendanceResponse,
)
from app.services import attendance_service

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


@router.get("/roster", response_model=AttendanceRosterResponse)
def get_roster(
    batch_id: int = Query(...),
    class_date: date = Query(...),
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> AttendanceRosterResponse:
    """Admin or assigned Instructor: get batch roster with attendance for a date."""
    return AttendanceRosterResponse(
        **attendance_service.get_roster_for_date(db, batch_id, class_date, current_user)
    )


@router.get("/daily", response_model=AttendanceRosterResponse)
def get_daily_view(
    batch_id: int = Query(...),
    class_date: date = Query(...),
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> AttendanceRosterResponse:
    """Admin or assigned Instructor: daily attendance view for a batch."""
    return AttendanceRosterResponse(
        **attendance_service.get_roster_for_date(db, batch_id, class_date, current_user)
    )


@router.post("", response_model=AttendanceRecordResponse, status_code=status.HTTP_201_CREATED)
def create_single_attendance(
    payload: AttendanceSingleCreate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> AttendanceRecordResponse:
    """Admin or assigned Instructor: record single attendance (409 on duplicate)."""
    return AttendanceRecordResponse(
        **attendance_service.create_single_attendance(db, payload, current_user)
    )


@router.post("/bulk", response_model=AttendanceRosterResponse)
def bulk_mark_attendance(
    payload: AttendanceBulkRequest,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> AttendanceRosterResponse:
    """Admin or assigned Instructor: bulk upsert attendance with audit logging."""
    return AttendanceRosterResponse(
        **attendance_service.bulk_upsert_attendance(db, payload, current_user)
    )


@router.get("/me", response_model=StudentAttendanceResponse)
def get_my_attendance(
    batch_id: int | None = Query(default=None),
    current_user: User = Depends(require_role(["Student"])),
    db: Session = Depends(get_db),
) -> StudentAttendanceResponse:
    """Student: view own attendance history, monthly summary, and percentage."""
    return StudentAttendanceResponse(
        **attendance_service.compute_student_attendance_summary(
            db, current_user.id, batch_id=batch_id
        )
    )
