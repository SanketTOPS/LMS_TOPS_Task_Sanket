from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models import BatchStatus, User
from app.schemas.batch import (
    BatchCreate,
    BatchEnrollRequest,
    BatchResponse,
    BatchRosterResponse,
    BatchUpdate,
    PaginatedBatchesResponse,
)
from app.services import batch_service

router = APIRouter(prefix="/api/batches", tags=["Batches"])


@router.get("", response_model=PaginatedBatchesResponse)
def list_batches(
    q: str | None = Query(default=None),
    course_id: int | None = Query(default=None),
    instructor_id: int | None = Query(default=None),
    status_filter: Literal["upcoming", "active", "closed", "archived"] | None = Query(default=None, alias="status"),
    sort_by: Literal["id", "name", "code", "start_date", "status", "created_at"] = Query(default="created_at"),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedBatchesResponse:
    """List batches scoped by role (Admin: all, Instructor: assigned, Student: enrolled)."""
    return PaginatedBatchesResponse(
        **batch_service.list_batches(
            db,
            current_user,
            q=q,
            course_id=course_id,
            instructor_id=instructor_id,
            status_filter=status_filter,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
    )


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: BatchCreate,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> BatchResponse:
    """Admin: create a new batch."""
    return BatchResponse(**batch_service.create_batch(db, payload))


@router.get("/{batch_id}", response_model=BatchResponse)
def get_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BatchResponse:
    """Get batch details (role-scoped)."""
    return BatchResponse(**batch_service.get_batch(db, batch_id, current_user))


@router.put("/{batch_id}", response_model=BatchResponse)
def update_batch(
    batch_id: int,
    payload: BatchUpdate,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> BatchResponse:
    """Admin: update batch details."""
    return BatchResponse(**batch_service.update_batch(db, batch_id, payload))


@router.patch("/{batch_id}/close", response_model=BatchResponse)
def close_batch(
    batch_id: int,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> BatchResponse:
    """Admin: close a batch."""
    return BatchResponse(**batch_service.set_batch_status(db, batch_id, BatchStatus.CLOSED))


@router.patch("/{batch_id}/archive", response_model=BatchResponse)
def archive_batch(
    batch_id: int,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> BatchResponse:
    """Admin: archive a batch."""
    return BatchResponse(**batch_service.set_batch_status(db, batch_id, BatchStatus.ARCHIVED))


@router.get("/{batch_id}/roster", response_model=BatchRosterResponse)
def get_batch_roster(
    batch_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> BatchRosterResponse:
    """Admin or assigned Instructor: view batch student roster."""
    return BatchRosterResponse(**batch_service.get_batch_roster(db, batch_id, current_user))


@router.post("/{batch_id}/students", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def add_student_to_batch(
    batch_id: int,
    payload: BatchEnrollRequest,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> BatchResponse:
    """Admin: transactionally enroll a student in course + batch with capacity & duplicate checks."""
    return BatchResponse(**batch_service.add_student_to_batch(db, batch_id, payload.student_id))


@router.delete("/{batch_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_student_from_batch(
    batch_id: int,
    student_id: int,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> None:
    """Admin: remove a student from a batch."""
    batch_service.remove_student_from_batch(db, batch_id, student_id)
