from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.certificate import (
    CertificateGenerateRequest,
    CertificateResponse,
    CertificateVerifyResponse,
    StudentCertificateEligibilityItem,
)
from app.services import certificate_service

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


@router.post("/generate", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
def generate_certificate(
    payload: CertificateGenerateRequest,
    current_user: User = Depends(require_role(["Admin", "Student"])),
    db: Session = Depends(get_db),
) -> CertificateResponse:
    """Generate completion certificate if academic rules are met (reusing progress criteria)."""
    return CertificateResponse(
        **certificate_service.generate_certificate(db, payload, current_user)
    )


@router.get("/me", response_model=list[StudentCertificateEligibilityItem])
def get_my_certificates(
    current_user: User = Depends(require_role(["Student"])),
    db: Session = Depends(get_db),
) -> list[StudentCertificateEligibilityItem]:
    """Student: view certificates and course completion eligibility checklist."""
    return [
        StudentCertificateEligibilityItem(**item)
        for item in certificate_service.get_student_certificates_me(db, current_user)
    ]


@router.get("", response_model=list[CertificateResponse])
def list_certificates(
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> list[CertificateResponse]:
    """Admin: view all certificates issued across all courses and students."""
    return [
        CertificateResponse(**item)
        for item in certificate_service.list_all_certificates(db)
    ]


@router.get("/verify/{code}", response_model=CertificateVerifyResponse)
def verify_certificate_public(
    code: str,
    db: Session = Depends(get_db),
) -> CertificateVerifyResponse:
    """Public endpoint: verify certificate validity by code or certificate number."""
    return CertificateVerifyResponse(**certificate_service.verify_certificate(db, code))


@router.get("/{certificate_id}/download")
def download_certificate(
    certificate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download official PDF Certificate of Completion (Student own or Admin)."""
    pdf_bytes, filename = certificate_service.get_certificate_download(
        db, certificate_id, current_user
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
