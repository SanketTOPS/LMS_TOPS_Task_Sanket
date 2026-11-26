from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import (
    AdminResetPasswordRequest,
    PaginatedUsersResponse,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services import user_service

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
    dependencies=[Depends(require_role(["Admin"]))],
)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Admin: create a new user."""
    user = user_service.create_user(db, payload)
    return UserResponse.model_validate(user)


@router.get("", response_model=PaginatedUsersResponse)
def list_users(
    q: str | None = Query(default=None, description="Search by name or email"),
    role: Literal["Admin", "Instructor", "Student"] | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    sort_by: Literal["id", "full_name", "email", "is_active", "created_at"] = Query(default="created_at"),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedUsersResponse:
    """Admin: list users with search, role/status filters, sorting, and pagination."""
    result = user_service.list_users(
        db,
        q=q,
        role_name=role,
        is_active=is_active,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    return PaginatedUsersResponse(
        items=[UserResponse.model_validate(u) for u in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Admin: update user details or role."""
    user = user_service.update_user(db, user_id, payload)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    current_admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Admin: soft-delete (deactivate) a user."""
    user = user_service.deactivate_user(db, user_id, current_admin)
    return UserResponse.model_validate(user)


@router.post("/{user_id}/reset-password", response_model=MessageResponse)
def admin_reset_password(
    user_id: int,
    payload: AdminResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Admin: reset another user's password."""
    user_service.admin_reset_password(db, user_id, payload.new_password)
    return MessageResponse(detail="User password has been reset successfully.")
