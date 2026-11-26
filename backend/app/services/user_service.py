import math
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.middleware.error_handler import AppException
from app.models.user import Instructor, Role, User
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.utils.security import hash_password, validate_password_policy

ALLOWED_SORT_COLUMNS = {
    "id": User.id,
    "full_name": User.full_name,
    "email": User.email,
    "is_active": User.is_active,
    "created_at": User.created_at,
}


def list_users(
    db: Session,
    *,
    q: str | None = None,
    role_name: str | None = None,
    is_active: bool | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """Return paginated, filtered, and sorted user list."""
    stmt = select(User).options(joinedload(User.role))
    count_stmt = select(func.count(User.id))

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        search_filter = or_(User.full_name.ilike(pattern), User.email.ilike(pattern))
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    if role_name:
        stmt = stmt.join(Role).where(Role.name == role_name)
        count_stmt = count_stmt.join(Role).where(Role.name == role_name)

    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
        count_stmt = count_stmt.where(User.is_active == is_active)

    sort_col = ALLOWED_SORT_COLUMNS.get(sort_by, User.created_at)
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


def create_user(db: Session, payload: UserCreateRequest) -> User:
    """Create a new user (and Instructor profile if role is Instructor)."""
    normalized_email = payload.email.strip().lower()
    existing = db.scalar(select(User).where(User.email == normalized_email))
    if existing:
        raise AppException(
            status_code=409,
            detail="A user with this email already exists.",
            code="EMAIL_ALREADY_EXISTS",
        )

    validate_password_policy(payload.password)

    role = db.scalar(select(Role).where(Role.name == payload.role_name))
    if not role:
        raise AppException(
            status_code=400,
            detail=f"Role '{payload.role_name}' does not exist.",
            code="INVALID_ROLE",
        )

    user = User(
        role_id=role.id,
        full_name=payload.full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(payload.password),
        phone=payload.phone.strip() if payload.phone else None,
        is_active=payload.is_active,
    )
    db.add(user)
    db.flush()

    if role.name == "Instructor":
        db.add(Instructor(user_id=user.id, is_active=payload.is_active))

    db.commit()
    return db.scalar(select(User).options(joinedload(User.role)).where(User.id == user.id))


def update_user(db: Session, user_id: int, payload: UserUpdateRequest) -> User:
    """Update user fields, enforcing unique email and role transitions."""
    user = db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id))
    if not user:
        raise AppException(status_code=404, detail="User not found.", code="USER_NOT_FOUND")

    if payload.email is not None:
        normalized_email = payload.email.strip().lower()
        if normalized_email != user.email:
            duplicate = db.scalar(select(User).where(User.email == normalized_email))
            if duplicate:
                raise AppException(
                    status_code=409,
                    detail="A user with this email already exists.",
                    code="EMAIL_ALREADY_EXISTS",
                )
            user.email = normalized_email

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()

    if payload.phone is not None:
        user.phone = payload.phone.strip() or None

    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.role_name is not None:
        role = db.scalar(select(Role).where(Role.name == payload.role_name))
        if not role:
            raise AppException(
                status_code=400,
                detail=f"Role '{payload.role_name}' does not exist.",
                code="INVALID_ROLE",
            )
        user.role_id = role.id
        if role.name == "Instructor":
            existing_inst = db.scalar(select(Instructor).where(Instructor.user_id == user.id))
            if not existing_inst:
                db.add(Instructor(user_id=user.id, is_active=user.is_active))

    db.commit()
    return db.scalar(select(User).options(joinedload(User.role)).where(User.id == user.id))


def deactivate_user(db: Session, user_id: int, current_admin: User) -> User:
    """Soft-delete (deactivate) a user account."""
    if user_id == current_admin.id:
        raise AppException(
            status_code=400,
            detail="You cannot deactivate your own account.",
            code="CANNOT_DEACTIVATE_SELF",
        )

    user = db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id))
    if not user:
        raise AppException(status_code=404, detail="User not found.", code="USER_NOT_FOUND")

    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


def admin_reset_password(db: Session, user_id: int, new_password: str) -> None:
    """Allow an Admin to reset a user's password."""
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise AppException(status_code=404, detail="User not found.", code="USER_NOT_FOUND")

    validate_password_policy(new_password)
    user.password_hash = hash_password(new_password)
    db.commit()
