from datetime import datetime, timezone
from decimal import Decimal
import math
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.middleware.error_handler import AppException
from app.models import (
    Assignment,
    AssignmentFeedback,
    Batch,
    BatchStudent,
    Course,
    Enrollment,
    Instructor,
    Submission,
    SubmissionStatus,
    SubmissionVersion,
    User,
)
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate, EvaluateSubmissionRequest
from app.services.lecture_service import (
    ensure_course_read_access,
    ensure_course_write_access,
)
from app.services.storage_service import (
    STUDY_MATERIAL_EXTENSIONS,
    get_storage_backend,
    validate_and_save_upload,
)

ALLOWED_ASSIGNMENT_SORT = {
    "id": Assignment.id,
    "title": Assignment.title,
    "due_date": Assignment.due_date,
    "created_at": Assignment.created_at,
}


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _serialize_submission(db: Session, sub: Submission) -> dict:
    student = db.scalar(select(User).where(User.id == sub.student_id))
    versions = list(
        db.scalars(
            select(SubmissionVersion)
            .where(SubmissionVersion.submission_id == sub.id)
            .order_by(SubmissionVersion.version_number.desc())
        ).all()
    )
    fb_rows = db.execute(
        select(AssignmentFeedback, User)
        .join(User, User.id == AssignmentFeedback.instructor_id)
        .where(AssignmentFeedback.submission_id == sub.id)
        .order_by(AssignmentFeedback.created_at.desc())
    ).all()

    return {
        "id": sub.id,
        "assignment_id": sub.assignment_id,
        "student_id": sub.student_id,
        "student_name": student.full_name if student else None,
        "student_email": student.email if student else None,
        "submission_text": sub.submission_text,
        "file_name": sub.file_name,
        "file_url": sub.file_url,
        "file_size_bytes": sub.file_size_bytes,
        "submitted_at": sub.submitted_at,
        "marks_obtained": sub.marks_obtained,
        "status": sub.status.value if hasattr(sub.status, "value") else sub.status,
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "submission_text": v.submission_text,
                "file_name": v.file_name,
                "file_url": v.file_url,
                "file_size_bytes": v.file_size_bytes,
                "submitted_at": v.submitted_at,
                "status": v.status.value if hasattr(v.status, "value") else v.status,
            }
            for v in versions
        ],
        "feedback": [
            {
                "id": fb.id,
                "submission_id": fb.submission_id,
                "instructor_id": fb.instructor_id,
                "instructor_name": u.full_name,
                "comments": fb.comments,
                "marks_awarded": fb.marks_awarded,
                "created_at": fb.created_at,
            }
            for fb, u in fb_rows
        ],
    }


def _serialize_assignment(db: Session, a: Assignment, student_id: int | None = None) -> dict:
    course_title = db.scalar(select(Course.title).where(Course.id == a.course_id))
    batch_name = (
        db.scalar(select(Batch.name).where(Batch.id == a.batch_id))
        if a.batch_id
        else None
    )
    my_sub = None
    if student_id is not None:
        sub = db.scalar(
            select(Submission).where(
                Submission.assignment_id == a.id,
                Submission.student_id == student_id,
            )
        )
        if sub:
            my_sub = _serialize_submission(db, sub)

    return {
        "id": a.id,
        "course_id": a.course_id,
        "course_title": course_title,
        "batch_id": a.batch_id,
        "batch_name": batch_name,
        "module_id": a.module_id,
        "title": a.title,
        "description": a.description,
        "attachment_name": a.attachment_name,
        "attachment_url": a.attachment_url,
        "max_marks": a.max_marks,
        "due_date": a.due_date,
        "allow_late": a.allow_late,
        "created_by": a.created_by,
        "created_at": a.created_at,
        "updated_at": a.updated_at,
        "my_submission": my_sub,
    }


def _ensure_student_assignment_access(db: Session, assignment: Assignment, student_id: int) -> None:
    if assignment.batch_id is not None:
        in_batch = db.scalar(
            select(BatchStudent.id).where(
                BatchStudent.batch_id == assignment.batch_id,
                BatchStudent.student_id == student_id,
                BatchStudent.is_active == True,  # noqa: E712
            )
        )
        if not in_batch:
            raise AppException(403, "You are not enrolled in this assignment's batch.", "FORBIDDEN")
    else:
        enrolled = db.scalar(
            select(Enrollment.id).where(
                Enrollment.course_id == assignment.course_id,
                Enrollment.student_id == student_id,
            )
        )
        if not enrolled:
            raise AppException(403, "You are not enrolled in this assignment's course.", "FORBIDDEN")


def list_assignments(
    db: Session,
    current_user: User,
    *,
    course_id: int | None = None,
    batch_id: int | None = None,
    sort_by: str = "due_date",
    sort_dir: str = "asc",
    page: int = 1,
    page_size: int = 10,
) -> dict:
    role_name = current_user.role.name if current_user.role else ""
    stmt = select(Assignment)
    count_stmt = select(func.count(Assignment.id))

    if role_name == "Instructor":
        inst_id = db.scalar(select(Instructor.id).where(Instructor.user_id == current_user.id))
        if not inst_id:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        inst_course_ids = select(Course.id).where(Course.instructor_id == inst_id)
        inst_batch_ids = select(Batch.id).where(Batch.instructor_id == inst_id)
        scope = or_(
            Assignment.course_id.in_(inst_course_ids),
            Assignment.batch_id.in_(inst_batch_ids),
        )
        stmt = stmt.where(scope)
        count_stmt = count_stmt.where(scope)
    elif role_name == "Student":
        my_course_ids = select(Enrollment.course_id).where(Enrollment.student_id == current_user.id)
        my_batch_ids = select(BatchStudent.batch_id).where(
            BatchStudent.student_id == current_user.id,
            BatchStudent.is_active == True,  # noqa: E712
        )
        scope = or_(
            Assignment.batch_id.in_(my_batch_ids),
            (Assignment.batch_id.is_(None)) & (Assignment.course_id.in_(my_course_ids)),
        )
        stmt = stmt.where(scope)
        count_stmt = count_stmt.where(scope)

    if course_id is not None:
        stmt = stmt.where(Assignment.course_id == course_id)
        count_stmt = count_stmt.where(Assignment.course_id == course_id)
    if batch_id is not None:
        stmt = stmt.where(Assignment.batch_id == batch_id)
        count_stmt = count_stmt.where(Assignment.batch_id == batch_id)

    sort_col = ALLOWED_ASSIGNMENT_SORT.get(sort_by, Assignment.due_date)
    order_fn = asc if sort_dir.lower() == "asc" else desc
    stmt = stmt.order_by(order_fn(sort_col))

    total = db.scalar(count_stmt) or 0
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    offset = (page - 1) * page_size

    rows = list(db.scalars(stmt.offset(offset).limit(page_size)).all())
    stu_id = current_user.id if role_name == "Student" else None
    return {
        "items": [_serialize_assignment(db, a, student_id=stu_id) for a in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def create_assignment(db: Session, payload: AssignmentCreate, current_user: User) -> dict:
    ensure_course_write_access(db, payload.course_id, current_user)
    if payload.batch_id is not None:
        batch = db.scalar(select(Batch).where(Batch.id == payload.batch_id))
        if not batch or batch.course_id != payload.course_id:
            raise AppException(400, "Batch does not belong to the specified course.", "INVALID_BATCH")

    a = Assignment(
        course_id=payload.course_id,
        batch_id=payload.batch_id,
        module_id=payload.module_id,
        title=payload.title.strip(),
        description=payload.description,
        max_marks=payload.max_marks,
        due_date=payload.due_date,
        allow_late=payload.allow_late,
        created_by=current_user.id,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return _serialize_assignment(db, a)


def get_assignment(db: Session, assignment_id: int, current_user: User) -> dict:
    a = db.scalar(select(Assignment).where(Assignment.id == assignment_id))
    if not a:
        raise AppException(404, "Assignment not found.", "ASSIGNMENT_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Student":
        _ensure_student_assignment_access(db, a, current_user.id)
        return _serialize_assignment(db, a, student_id=current_user.id)

    ensure_course_read_access(db, a.course_id, current_user)
    return _serialize_assignment(db, a)


def update_assignment(
    db: Session, assignment_id: int, payload: AssignmentUpdate, current_user: User
) -> dict:
    a = db.scalar(select(Assignment).where(Assignment.id == assignment_id))
    if not a:
        raise AppException(404, "Assignment not found.", "ASSIGNMENT_NOT_FOUND")
    ensure_course_write_access(db, a.course_id, current_user)

    if payload.batch_id is not None:
        a.batch_id = payload.batch_id
    if payload.module_id is not None:
        a.module_id = payload.module_id
    if payload.title is not None:
        a.title = payload.title.strip()
    if payload.description is not None:
        a.description = payload.description
    if payload.max_marks is not None:
        a.max_marks = payload.max_marks
    if payload.due_date is not None:
        a.due_date = payload.due_date
    if payload.allow_late is not None:
        a.allow_late = payload.allow_late

    db.commit()
    db.refresh(a)
    return _serialize_assignment(db, a)


def delete_assignment(db: Session, assignment_id: int, current_user: User) -> None:
    a = db.scalar(select(Assignment).where(Assignment.id == assignment_id))
    if not a:
        raise AppException(404, "Assignment not found.", "ASSIGNMENT_NOT_FOUND")
    ensure_course_write_access(db, a.course_id, current_user)

    has_subs = db.scalar(
        select(Submission.id).where(Submission.assignment_id == assignment_id)
    ) is not None
    if has_subs:
        raise AppException(
            409,
            "Cannot delete assignment that already has student submissions.",
            "ASSIGNMENT_HAS_SUBMISSIONS",
        )

    db.delete(a)
    db.commit()


async def upload_assignment_attachment(
    db: Session, assignment_id: int, file: UploadFile, current_user: User
) -> dict:
    a = db.scalar(select(Assignment).where(Assignment.id == assignment_id))
    if not a:
        raise AppException(404, "Assignment not found.", "ASSIGNMENT_NOT_FOUND")
    ensure_course_write_access(db, a.course_id, current_user)

    stored = await validate_and_save_upload(
        file,
        allowed_extensions=STUDY_MATERIAL_EXTENSIONS,
        subdir=f"assignments/{a.id}",
    )
    a.attachment_name = stored.original_name
    a.attachment_url = f"/api/assignments/{a.id}/attachment"
    db.commit()
    db.refresh(a)
    return _serialize_assignment(db, a)


def resolve_assignment_attachment(
    db: Session, assignment_id: int, current_user: User
) -> tuple[Assignment, Path]:
    a = db.scalar(select(Assignment).where(Assignment.id == assignment_id))
    if not a:
        raise AppException(404, "Assignment not found.", "ASSIGNMENT_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Student":
        _ensure_student_assignment_access(db, a, current_user.id)
    else:
        ensure_course_read_access(db, a.course_id, current_user)

    storage = get_storage_backend()
    att_dir = storage.resolve_path(f"assignments/{a.id}")
    if not att_dir.exists():
        raise AppException(404, "Attachment not found.", "FILE_NOT_FOUND")
    files = [p for p in att_dir.iterdir() if p.is_file()]
    if not files:
        raise AppException(404, "Attachment not found.", "FILE_NOT_FOUND")
    return a, files[-1]


async def submit_assignment(
    db: Session,
    *,
    assignment_id: int,
    submission_text: str | None,
    file: UploadFile | None,
    current_user: User,
) -> dict:
    a = db.scalar(select(Assignment).where(Assignment.id == assignment_id))
    if not a:
        raise AppException(404, "Assignment not found.", "ASSIGNMENT_NOT_FOUND")

    _ensure_student_assignment_access(db, a, current_user.id)

    if not submission_text and not file:
        raise AppException(422, "Provide submission text or upload a file.", "EMPTY_SUBMISSION")

    now = datetime.now(timezone.utc)
    is_late = now > _to_utc(a.due_date)
    if is_late and not a.allow_late:
        raise AppException(400, "Submission deadline has passed and late submissions are disabled.", "DEADLINE_PASSED")

    computed_status = SubmissionStatus.LATE_SUBMISSION if is_late else SubmissionStatus.SUBMITTED

    existing = db.scalar(
        select(Submission).where(
            Submission.assignment_id == a.id,
            Submission.student_id == current_user.id,
        )
    )
    if existing and existing.status == SubmissionStatus.EVALUATED:
        raise AppException(
            409,
            "Resubmission is not allowed after the assignment has been evaluated.",
            "ALREADY_EVALUATED",
        )

    if not existing:
        existing = Submission(
            assignment_id=a.id,
            student_id=current_user.id,
            status=computed_status,
        )
        db.add(existing)
        db.flush()

    next_version = (
        db.scalar(
            select(func.coalesce(func.max(SubmissionVersion.version_number), 0)).where(
                SubmissionVersion.submission_id == existing.id
            )
        )
        or 0
    ) + 1

    if file is not None:
        stored = await validate_and_save_upload(
            file,
            allowed_extensions=STUDY_MATERIAL_EXTENSIONS,
            subdir=f"submissions/{existing.id}/v{next_version}",
        )
        existing.file_name = stored.original_name
        existing.file_size_bytes = stored.size_bytes
        existing.file_url = f"/api/submissions/{existing.id}/download"

    if submission_text is not None:
        existing.submission_text = submission_text

    existing.submitted_at = now
    existing.status = computed_status

    db.add(
        SubmissionVersion(
            submission_id=existing.id,
            version_number=next_version,
            submission_text=existing.submission_text,
            file_name=existing.file_name,
            file_url=existing.file_url,
            file_size_bytes=existing.file_size_bytes,
            submitted_at=now,
            status=computed_status,
        )
    )
    db.commit()
    db.refresh(existing)
    return _serialize_submission(db, existing)


def list_assignment_submissions(
    db: Session, assignment_id: int, current_user: User
) -> list[dict]:
    a = db.scalar(select(Assignment).where(Assignment.id == assignment_id))
    if not a:
        raise AppException(404, "Assignment not found.", "ASSIGNMENT_NOT_FOUND")
    ensure_course_write_access(db, a.course_id, current_user)

    subs = list(
        db.scalars(
            select(Submission)
            .where(Submission.assignment_id == assignment_id)
            .order_by(Submission.submitted_at.desc())
        ).all()
    )
    return [_serialize_submission(db, s) for s in subs]


def evaluate_submission(
    db: Session,
    submission_id: int,
    payload: EvaluateSubmissionRequest,
    current_user: User,
) -> dict:
    sub = db.scalar(select(Submission).where(Submission.id == submission_id))
    if not sub:
        raise AppException(404, "Submission not found.", "SUBMISSION_NOT_FOUND")

    a = db.scalar(select(Assignment).where(Assignment.id == sub.assignment_id))
    ensure_course_write_access(db, a.course_id, current_user)

    if payload.marks > a.max_marks:
        raise AppException(
            422,
            f"Marks ({payload.marks}) cannot exceed max_marks ({a.max_marks}).",
            "MARKS_EXCEED_MAX",
        )

    sub.marks_obtained = payload.marks
    sub.status = SubmissionStatus.EVALUATED

    db.add(
        AssignmentFeedback(
            submission_id=sub.id,
            instructor_id=current_user.id,
            comments=payload.comments.strip(),
            marks_awarded=payload.marks,
        )
    )
    db.commit()
    db.refresh(sub)
    return _serialize_submission(db, sub)


def resolve_submission_download(
    db: Session, submission_id: int, current_user: User
) -> tuple[Submission, Path]:
    sub = db.scalar(select(Submission).where(Submission.id == submission_id))
    if not sub:
        raise AppException(404, "Submission not found.", "SUBMISSION_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Student":
        if sub.student_id != current_user.id:
            raise AppException(403, "You can only download your own submission.", "FORBIDDEN")
    else:
        a = db.scalar(select(Assignment).where(Assignment.id == sub.assignment_id))
        ensure_course_write_access(db, a.course_id, current_user)

    latest_ver = db.scalar(
        select(func.max(SubmissionVersion.version_number)).where(
            SubmissionVersion.submission_id == sub.id
        )
    ) or 1
    storage = get_storage_backend()
    sub_dir = storage.resolve_path(f"submissions/{sub.id}/v{latest_ver}")
    if not sub_dir.exists():
        raise AppException(404, "Submission file not found.", "FILE_NOT_FOUND")
    files = [p for p in sub_dir.iterdir() if p.is_file()]
    if not files:
        raise AppException(404, "Submission file not found.", "FILE_NOT_FOUND")
    return sub, files[0]
