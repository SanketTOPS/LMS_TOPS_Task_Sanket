import math
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.middleware.error_handler import AppException
from app.models import (
    Batch,
    BatchStudent,
    Course,
    Enrollment,
    Instructor,
    Role,
    User,
)
from app.schemas.student import StudentCreate, StudentUpdate
from app.utils.security import hash_password, validate_password_policy

ALLOWED_STUDENT_SORT = {
    "id": User.id,
    "full_name": User.full_name,
    "email": User.email,
    "is_active": User.is_active,
    "created_at": User.created_at,
}


def list_students(
    db: Session,
    current_user: User,
    *,
    q: str | None = None,
    is_active: bool | None = None,
    batch_id: int | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 10,
) -> dict:
    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Student":
        raise AppException(403, "Students cannot list other students.", "FORBIDDEN")

    stmt = select(User).join(Role, User.role_id == Role.id).where(Role.name == "Student")
    count_stmt = (
        select(func.count(User.id))
        .join(Role, User.role_id == Role.id)
        .where(Role.name == "Student")
    )

    if role_name == "Instructor":
        inst_id = db.scalar(select(Instructor.id).where(Instructor.user_id == current_user.id))
        if not inst_id:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        inst_student_ids = (
            select(BatchStudent.student_id)
            .join(Batch, Batch.id == BatchStudent.batch_id)
            .where(Batch.instructor_id == inst_id, BatchStudent.is_active == True)  # noqa: E712
        )
        stmt = stmt.where(User.id.in_(inst_student_ids))
        count_stmt = count_stmt.where(User.id.in_(inst_student_ids))

    if batch_id is not None:
        batch_student_ids = select(BatchStudent.student_id).where(
            BatchStudent.batch_id == batch_id,
            BatchStudent.is_active == True,  # noqa: E712
        )
        stmt = stmt.where(User.id.in_(batch_student_ids))
        count_stmt = count_stmt.where(User.id.in_(batch_student_ids))

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        search_filter = or_(User.full_name.ilike(pattern), User.email.ilike(pattern))
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
        count_stmt = count_stmt.where(User.is_active == is_active)

    sort_col = ALLOWED_STUDENT_SORT.get(sort_by, User.created_at)
    order_fn = asc if sort_dir.lower() == "asc" else desc
    stmt = stmt.order_by(order_fn(sort_col))

    total = db.scalar(count_stmt) or 0
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    offset = (page - 1) * page_size

    items = list(db.scalars(stmt.offset(offset).limit(page_size)).all())
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def create_student(db: Session, payload: StudentCreate) -> User:
    normalized_email = payload.email.strip().lower()
    if db.scalar(select(User).where(User.email == normalized_email)):
        raise AppException(409, "A user with this email already exists.", "EMAIL_ALREADY_EXISTS")

    validate_password_policy(payload.password)
    student_role = db.scalar(select(Role).where(Role.name == "Student"))
    if not student_role:
        raise AppException(500, "Student role is not configured.", "ROLE_NOT_FOUND")

    student = User(
        role_id=student_role.id,
        full_name=payload.full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(payload.password),
        phone=payload.phone.strip() if payload.phone else None,
        is_active=payload.is_active,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_student_detail(db: Session, student_id: int, current_user: User) -> dict:
    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Student" and current_user.id != student_id:
        raise AppException(403, "You can only view your own student profile.", "FORBIDDEN")

    student = db.scalar(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(User.id == student_id, Role.name == "Student")
    )
    if not student:
        raise AppException(404, "Student not found.", "STUDENT_NOT_FOUND")

    if role_name == "Instructor":
        inst_id = db.scalar(select(Instructor.id).where(Instructor.user_id == current_user.id))
        in_inst_batch = db.scalar(
            select(BatchStudent.id)
            .join(Batch, Batch.id == BatchStudent.batch_id)
            .where(
                Batch.instructor_id == inst_id,
                BatchStudent.student_id == student_id,
                BatchStudent.is_active == True,  # noqa: E712
            )
        )
        if not in_inst_batch:
            raise AppException(403, "Student is not in any of your batches.", "FORBIDDEN")

    enr_rows = db.execute(
        select(Enrollment, Course, Batch)
        .join(Course, Course.id == Enrollment.course_id)
        .outerjoin(Batch, Batch.id == Enrollment.batch_id)
        .where(Enrollment.student_id == student.id)
        .order_by(Enrollment.enrolled_at.desc())
    ).all()

    enrollments = [
        {
            "enrollment_id": enr.id,
            "course_id": c.id,
            "course_title": c.title,
            "course_code": c.code,
            "batch_id": b.id if b else None,
            "batch_name": b.name if b else None,
            "status": enr.status.value if hasattr(enr.status, "value") else enr.status,
            "enrolled_at": enr.enrolled_at,
        }
        for enr, c, b in enr_rows
    ]

    batch_rows = db.execute(
        select(Batch, Course)
        .join(BatchStudent, BatchStudent.batch_id == Batch.id)
        .join(Course, Course.id == Batch.course_id)
        .where(
            BatchStudent.student_id == student.id,
            BatchStudent.is_active == True,  # noqa: E712
        )
        .order_by(Batch.start_date.desc())
    ).all()

    batches = [
        {
            "batch_id": b.id,
            "batch_name": b.name,
            "batch_code": b.code,
            "course_title": c.title,
            "start_date": b.start_date,
            "end_date": b.end_date,
            "status": b.status.value if hasattr(b.status, "value") else b.status,
        }
        for b, c in batch_rows
    ]

    from app.services import attendance_service, progress_service

    att_summary = attendance_service.compute_student_attendance_summary(db, student.id)
    prog_data = progress_service.get_student_progress(db, student.id, current_user)

    return {
        "id": student.id,
        "full_name": student.full_name,
        "email": student.email,
        "phone": student.phone,
        "is_active": student.is_active,
        "created_at": student.created_at,
        "updated_at": student.updated_at,
        "enrollments": enrollments,
        "batches": batches,
        "attendance_percentage": att_summary["attendance_percentage"],
        "progress_percentage": prog_data["overall_progress_percentage"],
    }


def update_student(db: Session, student_id: int, payload: StudentUpdate) -> User:
    student = db.scalar(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(User.id == student_id, Role.name == "Student")
    )
    if not student:
        raise AppException(404, "Student not found.", "STUDENT_NOT_FOUND")

    if payload.email is not None:
        normalized_email = payload.email.strip().lower()
        if normalized_email != student.email:
            if db.scalar(select(User).where(User.email == normalized_email)):
                raise AppException(
                    409, "A user with this email already exists.", "EMAIL_ALREADY_EXISTS"
                )
            student.email = normalized_email

    if payload.full_name is not None:
        student.full_name = payload.full_name.strip()
    if payload.phone is not None:
        student.phone = payload.phone.strip() or None
    if payload.is_active is not None:
        student.is_active = payload.is_active

    db.commit()
    db.refresh(student)
    return student


def deactivate_student(db: Session, student_id: int) -> User:
    student = db.scalar(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(User.id == student_id, Role.name == "Student")
    )
    if not student:
        raise AppException(404, "Student not found.", "STUDENT_NOT_FOUND")

    student.is_active = False
    db.commit()
    db.refresh(student)
    return student
