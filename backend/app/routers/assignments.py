from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
    EvaluateSubmissionRequest,
    PaginatedAssignmentsResponse,
    SubmissionResponse,
)
from app.services import assignment_service

router = APIRouter(tags=["Assignments"])


@router.get("/api/assignments", response_model=PaginatedAssignmentsResponse)
def list_assignments(
    course_id: int | None = Query(default=None),
    batch_id: int | None = Query(default=None),
    sort_by: Literal["id", "title", "due_date", "created_at"] = Query(default="due_date"),
    sort_dir: Literal["asc", "desc"] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedAssignmentsResponse:
    """List assignments scoped by role."""
    return PaginatedAssignmentsResponse(
        **assignment_service.list_assignments(
            db,
            current_user,
            course_id=course_id,
            batch_id=batch_id,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
    )


@router.post("/api/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    """Admin or assigned Instructor: create an assignment."""
    return AssignmentResponse(**assignment_service.create_assignment(db, payload, current_user))


@router.get("/api/assignments/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    """Get assignment detail (role-scoped)."""
    return AssignmentResponse(**assignment_service.get_assignment(db, assignment_id, current_user))


@router.put("/api/assignments/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    """Admin or assigned Instructor: update assignment."""
    return AssignmentResponse(
        **assignment_service.update_assignment(db, assignment_id, payload, current_user)
    )


@router.delete("/api/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> None:
    """Admin or assigned Instructor: delete assignment (409 if submissions exist)."""
    assignment_service.delete_assignment(db, assignment_id, current_user)


@router.post("/api/assignments/{assignment_id}/attachment", response_model=AssignmentResponse)
async def upload_assignment_attachment(
    assignment_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    """Admin or assigned Instructor: upload reference attachment for an assignment."""
    data = await assignment_service.upload_assignment_attachment(db, assignment_id, file, current_user)
    return AssignmentResponse(**data)


@router.get("/api/assignments/{assignment_id}/attachment")
def download_assignment_attachment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Private download for assignment reference file."""
    assignment, path = assignment_service.resolve_assignment_attachment(db, assignment_id, current_user)
    return FileResponse(path=str(path), filename=assignment.attachment_name or path.name)


@router.get("/api/assignments/{assignment_id}/submissions", response_model=list[SubmissionResponse])
def list_submissions(
    assignment_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> list[SubmissionResponse]:
    """Admin or assigned Instructor: view all student submissions for an assignment."""
    return [
        SubmissionResponse(**s)
        for s in assignment_service.list_assignment_submissions(db, assignment_id, current_user)
    ]


@router.post("/api/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_assignment(
    assignment_id: int = Form(...),
    submission_text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    current_user: User = Depends(require_role(["Student"])),
    db: Session = Depends(get_db),
) -> SubmissionResponse:
    """Student: submit or resubmit an assignment (with server timestamp & late status)."""
    data = await assignment_service.submit_assignment(
        db,
        assignment_id=assignment_id,
        submission_text=submission_text,
        file=file,
        current_user=current_user,
    )
    return SubmissionResponse(**data)


@router.post("/api/submissions/{submission_id}/evaluate", response_model=SubmissionResponse)
def evaluate_submission(
    submission_id: int,
    payload: EvaluateSubmissionRequest,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> SubmissionResponse:
    """Admin or assigned Instructor: grade submission (0..max_marks) and record feedback."""
    return SubmissionResponse(
        **assignment_service.evaluate_submission(db, submission_id, payload, current_user)
    )


@router.get("/api/submissions/{submission_id}/download")
def download_submission(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Private download for a student submission file."""
    sub, path = assignment_service.resolve_submission_download(db, submission_id, current_user)
    return FileResponse(path=str(path), filename=sub.file_name or path.name)
