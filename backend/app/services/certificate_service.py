from datetime import datetime, timezone
import secrets
from pathlib import Path
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.middleware.error_handler import AppException
from app.models import BatchStudent, Certificate, Course, Enrollment, Role, User
from app.schemas.certificate import (
    CertificateGenerateRequest,
    CertificateResponse,
    CertificateVerifyResponse,
    StudentCertificateEligibilityItem,
)
from app.services import progress_service
from app.services.storage_service import get_storage_backend
from app.utils.pdf_generator import generate_certificate_pdf


def generate_certificate_number() -> str:
    year = datetime.now(timezone.utc).year
    suffix = secrets.token_hex(4).upper()
    return f"LMS-{year}-{suffix}"


def generate_verification_code() -> str:
    return f"VER-{secrets.token_hex(6).upper()}"


def generate_certificate(
    db: Session,
    payload: CertificateGenerateRequest,
    current_user: User,
) -> dict:
    """Generate certificate only when course completion rules are verified."""
    is_admin = current_user.role and current_user.role.name == "Admin"
    is_student = current_user.role and current_user.role.name == "Student"

    if is_student:
        target_student_id = current_user.id
    elif is_admin:
        if not payload.student_id:
            raise AppException(400, "student_id is required when generating as admin.", "STUDENT_ID_REQUIRED")
        target_student_id = payload.student_id
    else:
        raise AppException(403, "Only students or administrators can generate certificates.", "FORBIDDEN")

    student = db.scalar(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(User.id == target_student_id, Role.name == "Student")
    )
    if not student:
        raise AppException(404, "Student not found.", "STUDENT_NOT_FOUND")

    course = db.get(Course, payload.course_id)
    if not course:
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")

    # 1. Check duplicate certificate
    existing = db.scalar(
        select(Certificate).where(
            Certificate.student_id == target_student_id,
            Certificate.course_id == payload.course_id,
        )
    )
    if existing:
        raise AppException(409, "Certificate already generated for this course.", "DUPLICATE_CERTIFICATE")

    # 2. Check academic completion rules via progress service
    progress_data = progress_service.get_student_progress(db, target_student_id, current_user)
    course_item = next(
        (c for c in progress_data["courses"] if c["course_id"] == payload.course_id),
        None,
    )

    if not course_item or not course_item["is_complete"]:
        details = []
        if course_item:
            if course_item["course_progress_percentage"] < 80.0:
                details.append(f"Progress is {course_item['course_progress_percentage']:.1f}% (required >= 80%)")
            if course_item["attendance_percentage"] < 75.0:
                details.append(f"Attendance is {course_item['attendance_percentage']:.1f}% (required >= 75%)")
            if not course_item["all_quizzes_attempted"]:
                details.append(f"Not all quizzes attempted ({course_item['quizzes_attempted']}/{course_item['quizzes_total']})")
        reason = "; ".join(details) if details else "Student is not enrolled or active in this course"
        raise AppException(
            400,
            f"Student is not eligible for certificate: {reason}.",
            "NOT_ELIGIBLE_FOR_CERTIFICATE",
        )

    # 3. Find batch_id
    batch_id = db.scalar(
        select(Enrollment.batch_id).where(
            Enrollment.student_id == target_student_id,
            Enrollment.course_id == payload.course_id,
        )
    )

    cert_number = generate_certificate_number()
    ver_code = generate_verification_code()
    issued_at = datetime.now(timezone.utc)

    # 4. Generate PDF bytes and save
    pdf_bytes = generate_certificate_pdf(
        certificate_number=cert_number,
        verification_code=ver_code,
        student_name=student.full_name,
        course_title=course.title,
        course_code=course.code,
        issued_at=issued_at,
    )

    storage = get_storage_backend()
    stored_file = storage.save_bytes(
        pdf_bytes,
        f"Certificate_{cert_number}.pdf",
        "application/pdf",
        subdir="certificates",
    )

    # 5. Insert certificate record
    cert = Certificate(
        student_id=target_student_id,
        course_id=payload.course_id,
        batch_id=batch_id,
        certificate_number=cert_number,
        verification_code=ver_code,
        issued_at=issued_at,
        file_name=stored_file.original_name,
        file_url=stored_file.stored_key,
        issued_by=current_user.id,
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)

    return _format_certificate(cert, student=student, course=course, issuer=current_user)


def get_certificate_download(db: Session, certificate_id: int, current_user: User) -> tuple[bytes, str]:
    """Retrieve or dynamically re-render authorized certificate PDF."""
    cert = db.get(Certificate, certificate_id)
    if not cert:
        raise AppException(404, "Certificate not found.", "CERTIFICATE_NOT_FOUND")

    is_admin = current_user.role and current_user.role.name == "Admin"
    if not is_admin and cert.student_id != current_user.id:
        raise AppException(403, "You can only download your own certificates.", "FORBIDDEN")

    student = db.get(User, cert.student_id)
    course = db.get(Course, cert.course_id)

    # Check if stored file exists
    storage = get_storage_backend()
    if cert.file_url:
        try:
            path = storage.resolve_path(cert.file_url)
            if path.exists() and path.is_file():
                return path.read_bytes(), f"Certificate-{cert.certificate_number}.pdf"
        except Exception:
            pass

    # Fallback: dynamically re-generate PDF
    pdf_bytes = generate_certificate_pdf(
        certificate_number=cert.certificate_number,
        verification_code=cert.verification_code or f"VER-{cert.id}",
        student_name=student.full_name if student else "Student",
        course_title=course.title if course else "Course",
        course_code=course.code if course else "",
        issued_at=cert.issued_at,
    )
    return pdf_bytes, f"Certificate-{cert.certificate_number}.pdf"


def verify_certificate(db: Session, code: str) -> dict:
    """Public verification lookup by verification code or certificate number."""
    cleaned = code.strip().upper()
    cert = db.scalar(
        select(Certificate).where(
            (Certificate.verification_code == cleaned)
            | (Certificate.certificate_number == cleaned)
        )
    )

    if not cert:
        return {
            "valid": False,
            "certificate_number": None,
            "verification_code": None,
            "student_name": None,
            "course_title": None,
            "course_code": None,
            "issued_at": None,
            "message": "Certificate could not be verified. Please check the code and try again.",
        }

    student = db.get(User, cert.student_id)
    course = db.get(Course, cert.course_id)

    return {
        "valid": True,
        "certificate_number": cert.certificate_number,
        "verification_code": cert.verification_code,
        "student_name": student.full_name if student else "Student",
        "course_title": course.title if course else "Course",
        "course_code": course.code if course else "",
        "issued_at": cert.issued_at,
        "message": "Certificate is authentic and officially verified by the Institute.",
    }


def get_student_certificates_me(db: Session, current_user: User) -> list[dict]:
    """List certificates and eligibility statuses for courses enrolled by the student."""
    progress_data = progress_service.get_student_progress(db, current_user.id, current_user)

    # Fetch all certificates already issued for this student
    certs = db.scalars(
        select(Certificate).where(Certificate.student_id == current_user.id)
    ).all()
    cert_map = {c.course_id: c for c in certs}

    result = []
    for c_prog in progress_data["courses"]:
        c_id = c_prog["course_id"]
        cert = cert_map.get(c_id)
        formatted_cert = _format_certificate(cert) if cert else None

        result.append(
            {
                "course_id": c_id,
                "course_title": c_prog["course_title"],
                "course_code": c_prog["course_code"],
                "is_eligible": c_prog["is_complete"],
                "course_progress_percentage": c_prog["course_progress_percentage"],
                "attendance_percentage": c_prog["attendance_percentage"],
                "all_quizzes_attempted": c_prog["all_quizzes_attempted"],
                "certificate": formatted_cert,
            }
        )
    return result


def list_all_certificates(db: Session) -> list[dict]:
    """Admin endpoint to view all issued certificates across the institute."""
    certs = db.scalars(select(Certificate).order_by(desc(Certificate.issued_at))).all()
    return [_format_certificate(c) for c in certs]


def _format_certificate(
    cert: Certificate,
    *,
    student: User | None = None,
    course: Course | None = None,
    issuer: User | None = None,
) -> dict:
    student_obj = student or (cert.student if hasattr(cert, "student") else None)
    course_obj = course or (cert.course if hasattr(cert, "course") else None)

    return {
        "id": cert.id,
        "student_id": cert.student_id,
        "student_name": student_obj.full_name if student_obj else f"Student #{cert.student_id}",
        "student_email": student_obj.email if student_obj else "",
        "course_id": cert.course_id,
        "course_title": course_obj.title if course_obj else f"Course #{cert.course_id}",
        "course_code": course_obj.code if course_obj else "",
        "batch_id": cert.batch_id,
        "batch_name": f"Batch #{cert.batch_id}" if cert.batch_id else None,
        "certificate_number": cert.certificate_number,
        "verification_code": cert.verification_code or "",
        "issued_at": cert.issued_at,
        "file_name": cert.file_name,
        "file_url": cert.file_url,
        "issued_by": cert.issued_by,
        "issued_by_name": issuer.full_name if issuer else None,
    }
