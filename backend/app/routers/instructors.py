from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.instructor import (
    InstructorAssignRequest,
    InstructorBatchSummary,
    InstructorCreate,
    InstructorResponse,
    InstructorUpdate,
    PaginatedInstructorsResponse,
)
from app.services import instructor_service

router = APIRouter(prefix="/api/instructors", tags=["Instructors"])


@router.get("", response_model=PaginatedInstructorsResponse)
def list_instructors(
    q: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    sort_by: Literal["id", "full_name", "email", "experience_years", "created_at"] = Query(default="created_at"),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> PaginatedInstructorsResponse:
    """Admin: list instructors with search and pagination."""
    return PaginatedInstructorsResponse(
        **instructor_service.list_instructors(
            db,
            q=q,
            is_active=is_active,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/me", response_model=InstructorResponse)
def get_my_instructor_profile(
    current_user: User = Depends(require_role(["Instructor"])),
    db: Session = Depends(get_db),
) -> InstructorResponse:
    """Instructor: view own instructor profile."""
    return InstructorResponse(**instructor_service.get_my_instructor_profile(db, current_user))


@router.post("", response_model=InstructorResponse, status_code=status.HTTP_201_CREATED)
def create_instructor(
    payload: InstructorCreate,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> InstructorResponse:
    """Admin: create an instructor profile (and user if user_id omitted)."""
    return InstructorResponse(**instructor_service.create_instructor(db, payload))


@router.get("/{instructor_id}", response_model=InstructorResponse)
def get_instructor(
    instructor_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> InstructorResponse:
    """Admin or own Instructor: view instructor profile."""
    return InstructorResponse(**instructor_service.get_instructor(db, instructor_id, current_user))


@router.put("/{instructor_id}", response_model=InstructorResponse)
def update_instructor(
    instructor_id: int,
    payload: InstructorUpdate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> InstructorResponse:
    """Admin or own Instructor: update instructor profile."""
    return InstructorResponse(
        **instructor_service.update_instructor(db, instructor_id, payload, current_user)
    )


@router.get("/{instructor_id}/batches", response_model=list[InstructorBatchSummary])
def get_instructor_batches(
    instructor_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> list[InstructorBatchSummary]:
    """Admin or own Instructor: list batches assigned to this instructor."""
    return [
        InstructorBatchSummary(**b)
        for b in instructor_service.get_instructor_batches(db, instructor_id, current_user)
    ]


@router.post("/{instructor_id}/assign", response_model=InstructorResponse)
def assign_instructor(
    instructor_id: int,
    payload: InstructorAssignRequest,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> InstructorResponse:
    """Admin: assign an instructor to a course and/or batch."""
    return InstructorResponse(**instructor_service.assign_instructor(db, instructor_id, payload))
