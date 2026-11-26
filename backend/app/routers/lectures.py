from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.lecture import (
    CourseProgressResponse,
    LectureCreate,
    LectureProgressResponse,
    LectureReorderRequest,
    LectureResponse,
    LectureUpdate,
)
from app.services import lecture_service

router = APIRouter(tags=["Lectures"])


@router.get("/api/courses/{course_id}/lectures", response_model=list[LectureResponse])
def list_course_lectures(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LectureResponse]:
    """List lectures for a course (Admin, assigned Instructor, or enrolled Student)."""
    items = lecture_service.list_course_lectures(db, course_id, current_user)
    return [LectureResponse(**item) for item in items]


@router.get("/api/courses/{course_id}/progress", response_model=CourseProgressResponse)
def get_course_progress(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseProgressResponse:
    """Get lecture completion progress for a course."""
    return CourseProgressResponse(**lecture_service.get_course_progress(db, course_id, current_user))


@router.post("/api/lectures", response_model=LectureResponse, status_code=status.HTTP_201_CREATED)
def create_lecture(
    payload: LectureCreate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> LectureResponse:
    """Admin or assigned Instructor: create a lecture."""
    return LectureResponse(**lecture_service.create_lecture(db, payload, current_user))


@router.post("/api/lectures/reorder", response_model=list[LectureResponse])
def reorder_lectures(
    payload: LectureReorderRequest,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> list[LectureResponse]:
    """Admin or assigned Instructor: reorder lectures within a module."""
    items = lecture_service.reorder_lectures(
        db, payload.module_id, payload.lecture_ids, current_user
    )
    return [LectureResponse(**item) for item in items]


@router.get("/api/lectures/{lecture_id}", response_model=LectureResponse)
def get_lecture(
    lecture_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LectureResponse:
    """Get lecture detail (Admin, assigned Instructor, or enrolled Student)."""
    return LectureResponse(**lecture_service.get_lecture(db, lecture_id, current_user))


@router.put("/api/lectures/{lecture_id}", response_model=LectureResponse)
def update_lecture(
    lecture_id: int,
    payload: LectureUpdate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> LectureResponse:
    """Admin or assigned Instructor: update lecture."""
    return LectureResponse(**lecture_service.update_lecture(db, lecture_id, payload, current_user))


@router.delete("/api/lectures/{lecture_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lecture(
    lecture_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> None:
    """Admin or assigned Instructor: delete an unused lecture."""
    lecture_service.delete_lecture(db, lecture_id, current_user)


@router.post("/api/lectures/{lecture_id}/video", response_model=LectureResponse)
async def upload_lecture_video(
    lecture_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> LectureResponse:
    """Admin or assigned Instructor: upload a video file for a lecture."""
    data = await lecture_service.upload_lecture_video(db, lecture_id, file, current_user)
    return LectureResponse(**data)


@router.get("/api/lectures/{lecture_id}/video")
def download_lecture_video(
    lecture_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Private authenticated access to uploaded lecture video."""
    path = lecture_service.resolve_lecture_video_path(db, lecture_id, current_user)
    return FileResponse(path=str(path), filename=path.name)


@router.post("/api/lectures/{lecture_id}/complete", response_model=LectureProgressResponse)
def complete_lecture(
    lecture_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LectureProgressResponse:
    """Idempotently mark a lecture as completed for the current student."""
    progress = lecture_service.mark_lecture_complete(db, lecture_id, current_user)
    return LectureProgressResponse.model_validate(progress)
