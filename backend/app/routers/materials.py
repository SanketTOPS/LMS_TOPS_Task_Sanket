from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.lecture import StudyMaterialResponse
from app.services import lecture_service

router = APIRouter(prefix="/api/materials", tags=["Study Materials"])


@router.post("", response_model=StudyMaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(
    course_id: int = Form(...),
    title: str = Form(...),
    module_id: int | None = Form(default=None),
    lecture_id: int | None = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> StudyMaterialResponse:
    """Admin or assigned Instructor: upload a study material (PDF, PPT/PPTX, DOCX, ZIP)."""
    material = await lecture_service.upload_study_material(
        db,
        course_id=course_id,
        module_id=module_id,
        lecture_id=lecture_id,
        title=title,
        file=file,
        current_user=current_user,
    )
    return StudyMaterialResponse.model_validate(material)


@router.get("/{material_id}/download")
def download_material(
    material_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Private download endpoint (checks Admin, assigned Instructor, or enrolled Student)."""
    material, path = lecture_service.resolve_material_download(db, material_id, current_user)
    return FileResponse(
        path=str(path),
        filename=material.file_name,
        media_type=material.mime_type or "application/octet-stream",
    )


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> None:
    """Admin or assigned Instructor: delete a study material."""
    lecture_service.delete_study_material(db, material_id, current_user)
