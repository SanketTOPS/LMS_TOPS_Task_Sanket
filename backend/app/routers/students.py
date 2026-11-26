from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.student import (
    PaginatedStudentsResponse,
    StudentCreate,
    StudentDetailResponse,
    StudentResponse,
    StudentUpdate,
)
from app.services import student_service

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("", response_model=PaginatedStudentsResponse)
def list_students(
    q: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    batch_id: int | None = Query(default=None),
    sort_by: Literal["id", "full_name", "email", "is_active", "created_at"] = Query(default="created_at"),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> PaginatedStudentsResponse:
    """Admin (all) or Instructor (students in assigned batches): list students."""
    res = student_service.list_students(
        db,
        current_user,
        q=q,
        is_active=is_active,
        batch_id=batch_id,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    return PaginatedStudentsResponse(
        items=[StudentResponse.model_validate(s) for s in res["items"]],
        total=res["total"],
        page=res["page"],
        page_size=res["page_size"],
        total_pages=res["total_pages"],
    )


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> StudentResponse:
    """Admin: create a new student account."""
    student = student_service.create_student(db, payload)
    return StudentResponse.model_validate(student)


@router.get("/{student_id}", response_model=StudentDetailResponse)
def get_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentDetailResponse:
    """Get student detail with enrollment history, batches, and attendance/progress stubs."""
    return StudentDetailResponse(**student_service.get_student_detail(db, student_id, current_user))


@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> StudentResponse:
    """Admin: update student details."""
    student = student_service.update_student(db, student_id, payload)
    return StudentResponse.model_validate(student)


@router.delete("/{student_id}", response_model=StudentResponse)
def deactivate_student(
    student_id: int,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> StudentResponse:
    """Admin: soft-delete (deactivate) a student."""
    student = student_service.deactivate_student(db, student_id)
    return StudentResponse.model_validate(student)
