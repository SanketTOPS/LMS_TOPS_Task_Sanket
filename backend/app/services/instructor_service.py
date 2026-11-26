import math
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.middleware.error_handler import AppException
from app.models import Batch, Course, Instructor, Role, User
from app.schemas.instructor import InstructorAssignRequest, InstructorCreate, InstructorUpdate
from app.utils.security import hash_password, validate_password_policy

ALLOWED_INSTRUCTOR_SORT = {
    "id": Instructor.id,
    "full_name": User.full_name,
    "email": User.email,
    "experience_years": Instructor.experience_years,
    "created_at": Instructor.created_at,
}


def _serialize_instructor(inst: Instructor, user: User) -> dict:
    return {
        "id": inst.id,
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "bio": inst.bio,
        "expertise": inst.expertise,
        "qualification": inst.qualification,
        "experience_years": inst.experience_years,
        "is_active": inst.is_active and user.is_active,
        "created_at": inst.created_at,
        "updated_at": inst.updated_at,
    }


def list_instructors(
    db: Session,
    *,
    q: str | None = None,
    is_active: bool | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 10,
) -> dict:
    stmt = select(Instructor, User).join(User, User.id == Instructor.user_id)
    count_stmt = select(func.count(Instructor.id)).join(User, User.id == Instructor.user_id)

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        search_filter = or_(
            User.full_name.ilike(pattern),
            User.email.ilike(pattern),
            Instructor.expertise.ilike(pattern),
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    if is_active is not None:
        stmt = stmt.where(Instructor.is_active == is_active)
        count_stmt = count_stmt.where(Instructor.is_active == is_active)

    sort_col = ALLOWED_INSTRUCTOR_SORT.get(sort_by, Instructor.created_at)
    order_fn = asc if sort_dir.lower() == "asc" else desc
    stmt = stmt.order_by(order_fn(sort_col))

    total = db.scalar(count_stmt) or 0
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    offset = (page - 1) * page_size

    rows = db.execute(stmt.offset(offset).limit(page_size)).all()
    return {
        "items": [_serialize_instructor(inst, user) for inst, user in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def create_instructor(db: Session, payload: InstructorCreate) -> dict:
    if payload.user_id is not None:
        user = db.scalar(select(User).where(User.id == payload.user_id))
        if not user:
            raise AppException(404, "User not found.", "USER_NOT_FOUND")
        if db.scalar(select(Instructor).where(Instructor.user_id == user.id)):
            raise AppException(
                409, "Instructor profile already exists for this user.", "INSTRUCTOR_EXISTS"
            )
    else:
        if not payload.email or not payload.full_name or not payload.password:
            raise AppException(
                422,
                "full_name, email, and password are required when user_id is omitted.",
                "VALIDATION_ERROR",
            )
        normalized_email = payload.email.strip().lower()
        if db.scalar(select(User).where(User.email == normalized_email)):
            raise AppException(409, "A user with this email already exists.", "EMAIL_ALREADY_EXISTS")

        validate_password_policy(payload.password)
        role = db.scalar(select(Role).where(Role.name == "Instructor"))
        if not role:
            raise AppException(500, "Instructor role is not configured.", "ROLE_NOT_FOUND")

        user = User(
            role_id=role.id,
            full_name=payload.full_name.strip(),
            email=normalized_email,
            password_hash=hash_password(payload.password),
            phone=payload.phone.strip() if payload.phone else None,
            is_active=True,
        )
        db.add(user)
        db.flush()

    inst = Instructor(
        user_id=user.id,
        bio=payload.bio,
        expertise=payload.expertise,
        qualification=payload.qualification,
        experience_years=payload.experience_years,
        is_active=True,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    db.refresh(user)
    return _serialize_instructor(inst, user)


def get_instructor(db: Session, instructor_id: int, current_user: User) -> dict:
    row = db.execute(
        select(Instructor, User)
        .join(User, User.id == Instructor.user_id)
        .where(Instructor.id == instructor_id)
    ).first()
    if not row:
        raise AppException(404, "Instructor not found.", "INSTRUCTOR_NOT_FOUND")
    inst, user = row

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Instructor" and inst.user_id != current_user.id:
        raise AppException(403, "You can only view your own instructor profile.", "FORBIDDEN")
    if role_name == "Student":
        raise AppException(403, "Students cannot access instructor management.", "FORBIDDEN")

    return _serialize_instructor(inst, user)


def get_my_instructor_profile(db: Session, current_user: User) -> dict:
    row = db.execute(
        select(Instructor, User)
        .join(User, User.id == Instructor.user_id)
        .where(Instructor.user_id == current_user.id)
    ).first()
    if not row:
        raise AppException(404, "Instructor profile not found.", "INSTRUCTOR_NOT_FOUND")
    return _serialize_instructor(row[0], row[1])


def update_instructor(
    db: Session, instructor_id: int, payload: InstructorUpdate, current_user: User
) -> dict:
    row = db.execute(
        select(Instructor, User)
        .join(User, User.id == Instructor.user_id)
        .where(Instructor.id == instructor_id)
    ).first()
    if not row:
        raise AppException(404, "Instructor not found.", "INSTRUCTOR_NOT_FOUND")
    inst, user = row

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Instructor" and inst.user_id != current_user.id:
        raise AppException(403, "You can only update your own instructor profile.", "FORBIDDEN")
    if role_name not in ("Admin", "Instructor"):
        raise AppException(403, "Forbidden.", "FORBIDDEN")

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.phone is not None:
        user.phone = payload.phone.strip() or None
    if payload.bio is not None:
        inst.bio = payload.bio
    if payload.expertise is not None:
        inst.expertise = payload.expertise
    if payload.qualification is not None:
        inst.qualification = payload.qualification
    if payload.experience_years is not None:
        inst.experience_years = payload.experience_years
    if payload.is_active is not None and role_name == "Admin":
        inst.is_active = payload.is_active

    db.commit()
    db.refresh(inst)
    db.refresh(user)
    return _serialize_instructor(inst, user)


def get_instructor_batches(db: Session, instructor_id: int, current_user: User) -> list[dict]:
    inst = db.scalar(select(Instructor).where(Instructor.id == instructor_id))
    if not inst:
        raise AppException(404, "Instructor not found.", "INSTRUCTOR_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Instructor" and inst.user_id != current_user.id:
        raise AppException(403, "You can only view your own assigned batches.", "FORBIDDEN")
    if role_name not in ("Admin", "Instructor"):
        raise AppException(403, "Forbidden.", "FORBIDDEN")

    rows = db.execute(
        select(Batch, Course)
        .join(Course, Course.id == Batch.course_id)
        .where(Batch.instructor_id == instructor_id)
        .order_by(Batch.start_date.desc())
    ).all()

    return [
        {
            "batch_id": b.id,
            "batch_name": b.name,
            "batch_code": b.code,
            "course_id": c.id,
            "course_title": c.title,
            "start_date": b.start_date,
            "end_date": b.end_date,
            "status": b.status.value if hasattr(b.status, "value") else b.status,
        }
        for b, c in rows
    ]


def assign_instructor(
    db: Session, instructor_id: int, payload: InstructorAssignRequest
) -> dict:
    row = db.execute(
        select(Instructor, User)
        .join(User, User.id == Instructor.user_id)
        .where(Instructor.id == instructor_id)
    ).first()
    if not row:
        raise AppException(404, "Instructor not found.", "INSTRUCTOR_NOT_FOUND")
    inst, user = row

    if payload.course_id is None and payload.batch_id is None:
        raise AppException(422, "Provide course_id or batch_id to assign.", "VALIDATION_ERROR")

    if payload.course_id is not None:
        course = db.scalar(select(Course).where(Course.id == payload.course_id))
        if not course:
            raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")
        course.instructor_id = instructor_id

    if payload.batch_id is not None:
        batch = db.scalar(select(Batch).where(Batch.id == payload.batch_id))
        if not batch:
            raise AppException(404, "Batch not found.", "BATCH_NOT_FOUND")
        batch.instructor_id = instructor_id

    db.commit()
    return _serialize_instructor(inst, user)
