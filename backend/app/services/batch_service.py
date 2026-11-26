import math
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.middleware.error_handler import AppException
from app.models import (
    Batch,
    BatchStatus,
    BatchStudent,
    Course,
    Enrollment,
    EnrollmentStatus,
    Instructor,
    User,
)
from app.schemas.batch import BatchCreate, BatchUpdate

ALLOWED_BATCH_SORT = {
    "id": Batch.id,
    "name": Batch.name,
    "code": Batch.code,
    "start_date": Batch.start_date,
    "status": Batch.status,
    "created_at": Batch.created_at,
}


def _serialize_batch(db: Session, batch: Batch) -> dict:
    course_title = db.scalar(select(Course.title).where(Course.id == batch.course_id))
    instructor_name = db.scalar(
        select(User.full_name)
        .join(Instructor, Instructor.user_id == User.id)
        .where(Instructor.id == batch.instructor_id)
    )
    enrolled_count = (
        db.scalar(
            select(func.count(BatchStudent.id)).where(
                BatchStudent.batch_id == batch.id,
                BatchStudent.is_active == True,  # noqa: E712
            )
        )
        or 0
    )
    return {
        "id": batch.id,
        "course_id": batch.course_id,
        "course_title": course_title,
        "instructor_id": batch.instructor_id,
        "instructor_name": instructor_name,
        "name": batch.name,
        "code": batch.code,
        "start_date": batch.start_date,
        "end_date": batch.end_date,
        "schedule_info": batch.schedule_info,
        "max_students": batch.max_students,
        "enrolled_count": enrolled_count,
        "status": batch.status.value if hasattr(batch.status, "value") else batch.status,
        "created_at": batch.created_at,
        "updated_at": batch.updated_at,
    }


def list_batches(
    db: Session,
    current_user: User,
    *,
    q: str | None = None,
    course_id: int | None = None,
    instructor_id: int | None = None,
    status_filter: str | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 10,
) -> dict:
    role_name = current_user.role.name if current_user.role else ""
    stmt = select(Batch)
    count_stmt = select(func.count(Batch.id))

    # Strict role scoping
    if role_name == "Instructor":
        inst_id = db.scalar(select(Instructor.id).where(Instructor.user_id == current_user.id))
        if not inst_id:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        stmt = stmt.where(Batch.instructor_id == inst_id)
        count_stmt = count_stmt.where(Batch.instructor_id == inst_id)
    elif role_name == "Student":
        my_batch_ids = select(BatchStudent.batch_id).where(
            BatchStudent.student_id == current_user.id,
            BatchStudent.is_active == True,  # noqa: E712
        )
        stmt = stmt.where(Batch.id.in_(my_batch_ids))
        count_stmt = count_stmt.where(Batch.id.in_(my_batch_ids))

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        search_filter = or_(Batch.name.ilike(pattern), Batch.code.ilike(pattern))
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    if course_id is not None:
        stmt = stmt.where(Batch.course_id == course_id)
        count_stmt = count_stmt.where(Batch.course_id == course_id)

    if instructor_id is not None and role_name == "Admin":
        stmt = stmt.where(Batch.instructor_id == instructor_id)
        count_stmt = count_stmt.where(Batch.instructor_id == instructor_id)

    if status_filter:
        try:
            enum_status = BatchStatus(status_filter)
        except ValueError as exc:
            raise AppException(400, f"Invalid batch status '{status_filter}'.", "INVALID_STATUS") from exc
        stmt = stmt.where(Batch.status == enum_status)
        count_stmt = count_stmt.where(Batch.status == enum_status)

    sort_col = ALLOWED_BATCH_SORT.get(sort_by, Batch.created_at)
    order_fn = asc if sort_dir.lower() == "asc" else desc
    stmt = stmt.order_by(order_fn(sort_col))

    total = db.scalar(count_stmt) or 0
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    offset = (page - 1) * page_size

    batches = list(db.scalars(stmt.offset(offset).limit(page_size)).all())
    return {
        "items": [_serialize_batch(db, b) for b in batches],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def create_batch(db: Session, payload: BatchCreate) -> dict:
    code = payload.code.strip().upper()
    if db.scalar(select(Batch).where(Batch.code == code)):
        raise AppException(409, "A batch with this code already exists.", "DUPLICATE_BATCH_CODE")

    if not db.scalar(select(Course.id).where(Course.id == payload.course_id)):
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")
    if not db.scalar(select(Instructor.id).where(Instructor.id == payload.instructor_id)):
        raise AppException(404, "Instructor not found.", "INSTRUCTOR_NOT_FOUND")

    batch = Batch(
        course_id=payload.course_id,
        instructor_id=payload.instructor_id,
        name=payload.name.strip(),
        code=code,
        start_date=payload.start_date,
        end_date=payload.end_date,
        schedule_info=payload.schedule_info,
        max_students=payload.max_students,
        status=BatchStatus(payload.status),
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return _serialize_batch(db, batch)


def get_batch(db: Session, batch_id: int, current_user: User) -> dict:
    batch = db.scalar(select(Batch).where(Batch.id == batch_id))
    if not batch:
        raise AppException(404, "Batch not found.", "BATCH_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Instructor":
        inst_id = db.scalar(select(Instructor.id).where(Instructor.user_id == current_user.id))
        if batch.instructor_id != inst_id:
            raise AppException(403, "You are not assigned to this batch.", "FORBIDDEN")
    elif role_name == "Student":
        in_batch = db.scalar(
            select(BatchStudent.id).where(
                BatchStudent.batch_id == batch.id,
                BatchStudent.student_id == current_user.id,
                BatchStudent.is_active == True,  # noqa: E712
            )
        )
        if not in_batch:
            raise AppException(403, "You are not enrolled in this batch.", "FORBIDDEN")

    return _serialize_batch(db, batch)


def update_batch(db: Session, batch_id: int, payload: BatchUpdate) -> dict:
    batch = db.scalar(select(Batch).where(Batch.id == batch_id))
    if not batch:
        raise AppException(404, "Batch not found.", "BATCH_NOT_FOUND")

    new_start = payload.start_date or batch.start_date
    new_end = payload.end_date if payload.end_date is not None else batch.end_date
    if new_end is not None and new_end <= new_start:
        raise AppException(422, "end_date must be strictly after start_date.", "INVALID_DATES")

    if payload.code is not None:
        new_code = payload.code.strip().upper()
        if new_code != batch.code and db.scalar(select(Batch).where(Batch.code == new_code)):
            raise AppException(409, "A batch with this code already exists.", "DUPLICATE_BATCH_CODE")
        batch.code = new_code

    if payload.course_id is not None:
        if not db.scalar(select(Course.id).where(Course.id == payload.course_id)):
            raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")
        batch.course_id = payload.course_id

    if payload.instructor_id is not None:
        if not db.scalar(select(Instructor.id).where(Instructor.id == payload.instructor_id)):
            raise AppException(404, "Instructor not found.", "INSTRUCTOR_NOT_FOUND")
        batch.instructor_id = payload.instructor_id

    if payload.name is not None:
        batch.name = payload.name.strip()
    if payload.start_date is not None:
        batch.start_date = payload.start_date
    if payload.end_date is not None:
        batch.end_date = payload.end_date
    if payload.schedule_info is not None:
        batch.schedule_info = payload.schedule_info
    if payload.max_students is not None:
        current_count = (
            db.scalar(
                select(func.count(BatchStudent.id)).where(
                    BatchStudent.batch_id == batch.id,
                    BatchStudent.is_active == True,  # noqa: E712
                )
            )
            or 0
        )
        if payload.max_students < current_count:
            raise AppException(
                409,
                f"Cannot reduce capacity below current enrolled count ({current_count}).",
                "CAPACITY_BELOW_ENROLLED",
            )
        batch.max_students = payload.max_students

    db.commit()
    db.refresh(batch)
    return _serialize_batch(db, batch)


def set_batch_status(db: Session, batch_id: int, status: BatchStatus) -> dict:
    batch = db.scalar(select(Batch).where(Batch.id == batch_id))
    if not batch:
        raise AppException(404, "Batch not found.", "BATCH_NOT_FOUND")
    batch.status = status
    db.commit()
    db.refresh(batch)
    return _serialize_batch(db, batch)


def get_batch_roster(db: Session, batch_id: int, current_user: User) -> dict:
    batch = db.scalar(select(Batch).where(Batch.id == batch_id))
    if not batch:
        raise AppException(404, "Batch not found.", "BATCH_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Instructor":
        inst_id = db.scalar(select(Instructor.id).where(Instructor.user_id == current_user.id))
        if batch.instructor_id != inst_id:
            raise AppException(403, "You are not assigned to this batch.", "FORBIDDEN")
    elif role_name != "Admin":
        raise AppException(403, "You do not have permission to view batch roster.", "FORBIDDEN")

    rows = db.execute(
        select(BatchStudent, User)
        .join(User, User.id == BatchStudent.student_id)
        .where(
            BatchStudent.batch_id == batch.id,
            BatchStudent.is_active == True,  # noqa: E712
        )
        .order_by(User.full_name.asc())
    ).all()

    students = [
        {
            "student_id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "joined_at": bs.joined_at,
            "is_active": bs.is_active,
        }
        for bs, u in rows
    ]
    return {
        "batch_id": batch.id,
        "batch_name": batch.name,
        "max_students": batch.max_students,
        "enrolled_count": len(students),
        "students": students,
    }


def add_student_to_batch(db: Session, batch_id: int, student_id: int) -> dict:
    """Transactionally enroll a student in the batch's course and add to batch_students."""
    batch = db.scalar(select(Batch).where(Batch.id == batch_id))
    if not batch:
        raise AppException(404, "Batch not found.", "BATCH_NOT_FOUND")

    if batch.status in (BatchStatus.CLOSED, BatchStatus.ARCHIVED):
        raise AppException(400, "Cannot enroll students into a closed or archived batch.", "BATCH_CLOSED")

    student = db.scalar(
        select(User)
        .options(joinedload(User.role))
        .where(User.id == student_id)
    )
    if not student or not student.role or student.role.name != "Student":
        raise AppException(404, "Student not found.", "STUDENT_NOT_FOUND")
    if not student.is_active:
        raise AppException(400, "Cannot enroll an inactive student.", "INACTIVE_STUDENT")

    existing_bs = db.scalar(
        select(BatchStudent).where(
            BatchStudent.batch_id == batch.id,
            BatchStudent.student_id == student.id,
        )
    )
    if existing_bs:
        raise AppException(
            409,
            "Student is already enrolled in this batch.",
            "DUPLICATE_ENROLLMENT",
        )

    current_count = (
        db.scalar(
            select(func.count(BatchStudent.id)).where(
                BatchStudent.batch_id == batch.id,
                BatchStudent.is_active == True,  # noqa: E712
            )
        )
        or 0
    )
    if current_count >= batch.max_students:
        raise AppException(
            409,
            f"Batch capacity ({batch.max_students}) is full.",
            "BATCH_CAPACITY_FULL",
        )

    # Transactional: ensure Enrollment exists for (student_id, batch.course_id), then add BatchStudent
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student.id,
            Enrollment.course_id == batch.course_id,
        )
    )
    if not enrollment:
        enrollment = Enrollment(
            student_id=student.id,
            course_id=batch.course_id,
            batch_id=batch.id,
            status=EnrollmentStatus.ACTIVE,
        )
        db.add(enrollment)
    elif enrollment.batch_id is None:
        enrollment.batch_id = batch.id

    db.add(BatchStudent(batch_id=batch.id, student_id=student.id, is_active=True))
    db.commit()
    return _serialize_batch(db, batch)


def remove_student_from_batch(db: Session, batch_id: int, student_id: int) -> None:
    bs = db.scalar(
        select(BatchStudent).where(
            BatchStudent.batch_id == batch_id,
            BatchStudent.student_id == student_id,
        )
    )
    if not bs:
        raise AppException(404, "Student is not enrolled in this batch.", "NOT_IN_BATCH")

    db.delete(bs)
    db.commit()
