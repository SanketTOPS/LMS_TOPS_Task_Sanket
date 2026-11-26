from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.course import (
    CourseCreate,
    CourseDetailResponse,
    CourseModuleCreate,
    CourseModuleResponse,
    CourseModuleUpdate,
    CourseResponse,
    CourseUpdate,
    PaginatedCoursesResponse,
)
from app.services import course_service

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("", response_model=PaginatedCoursesResponse)
def list_courses(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    status_filter: Literal["draft", "published", "archived"] | None = Query(default=None, alias="status"),
    sort_by: Literal["id", "title", "code", "category", "fee_amount", "status", "created_at"] = Query(default="created_at"),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedCoursesResponse:
    """List courses scoped by role (Admin: all, Instructor: assigned, Student: published/enrolled)."""
    return PaginatedCoursesResponse(
        **course_service.list_courses(
            db,
            current_user,
            q=q,
            category=category,
            status_filter=status_filter,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
    )


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    admin_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> CourseResponse:
    """Admin: create a new course."""
    return CourseResponse(**course_service.create_course(db, payload, admin_user))


@router.get("/{course_id}", response_model=CourseDetailResponse)
def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseDetailResponse:
    """Get course detail with modules, instructor, and enrollment info."""
    return CourseDetailResponse(**course_service.get_course_detail(db, course_id, current_user))


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> CourseResponse:
    """Admin (full) or assigned Instructor (description/thumbnail only) update course."""
    return CourseResponse(**course_service.update_course(db, course_id, payload, current_user))


@router.patch("/{course_id}/publish", response_model=CourseResponse)
def publish_course(
    course_id: int,
    publish: bool = Query(default=True),
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> CourseResponse:
    """Admin: publish or unpublish a course."""
    return CourseResponse(**course_service.set_course_publish(db, course_id, publish))


@router.patch("/{course_id}/archive", response_model=CourseResponse)
def archive_course(
    course_id: int,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> CourseResponse:
    """Admin: archive a course (soft delete)."""
    return CourseResponse(**course_service.archive_course(db, course_id))


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    _admin: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> None:
    """Admin: delete course only if no batches or enrollments exist (otherwise 409)."""
    course_service.delete_course(db, course_id)


@router.get("/{course_id}/modules", response_model=list[CourseModuleResponse])
def list_modules(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CourseModuleResponse]:
    """List modules for a course (role-scoped via course access)."""
    detail = course_service.get_course_detail(db, course_id, current_user)
    return [CourseModuleResponse.model_validate(m) for m in detail["modules"]]


@router.post("/{course_id}/modules", response_model=CourseModuleResponse, status_code=status.HTTP_201_CREATED)
def create_module(
    course_id: int,
    payload: CourseModuleCreate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> CourseModuleResponse:
    """Admin or assigned Instructor: add a module to a course."""
    mod = course_service.create_module(db, course_id, payload, current_user)
    return CourseModuleResponse.model_validate(mod)


@router.put("/{course_id}/modules/{module_id}", response_model=CourseModuleResponse)
def update_module(
    course_id: int,
    module_id: int,
    payload: CourseModuleUpdate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> CourseModuleResponse:
    """Admin or assigned Instructor: update a module."""
    mod = course_service.update_module(db, course_id, module_id, payload, current_user)
    return CourseModuleResponse.model_validate(mod)


@router.delete("/{course_id}/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(
    course_id: int,
    module_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> None:
    """Admin or assigned Instructor: delete an unused module."""
    course_service.delete_module(db, course_id, module_id, current_user)
