from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.progress import StudentProgressResponse
from app.services import progress_service

router = APIRouter(prefix="/api/progress", tags=["Progress"])


@router.get("/me", response_model=StudentProgressResponse)
def get_my_progress(
    current_user: User = Depends(require_role(["Student"])),
    db: Session = Depends(get_db),
) -> StudentProgressResponse:
    """Student: view own lecture, assignment, quiz, attendance, and completion metrics."""
    return StudentProgressResponse(
        **progress_service.get_student_progress(db, current_user.id, current_user)
    )


@router.get("/student/{student_id}", response_model=StudentProgressResponse)
def get_student_progress(
    student_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> StudentProgressResponse:
    """Admin or assigned Instructor: view a student's course progress metrics."""
    return StudentProgressResponse(
        **progress_service.get_student_progress(db, student_id, current_user)
    )
