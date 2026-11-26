from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.middleware.error_handler import AppException
from app.models.user import User
from app.utils.security import (
    create_access_token,
    create_reset_token,
    decode_token,
    hash_password,
    validate_password_policy,
    verify_password,
)


def authenticate_user(db: Session, email: str, password: str) -> tuple[str, User]:
    """Verify credentials and active status, returning (jwt_token, user)."""
    normalized_email = email.strip().lower()
    user = db.scalar(
        select(User)
        .options(joinedload(User.role))
        .where(User.email == normalized_email)
    )
    if not user or not verify_password(password, user.password_hash):
        raise AppException(
            status_code=401,
            detail="Invalid email or password.",
            code="INVALID_CREDENTIALS",
        )
    if not user.is_active:
        raise AppException(
            status_code=403,
            detail="Account is deactivated. Please contact an administrator.",
            code="INACTIVE_USER",
        )

    role_name = user.role.name if user.role else ""
    token = create_access_token(user.id, role_name)
    return token, user


def initiate_password_reset(db: Session, email: str) -> None:
    """Generate a time-limited reset token and print dev link when in development."""
    normalized_email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if user and user.is_active:
        reset_token = create_reset_token(user.id)
        if settings.APP_ENV == "development" or settings.DEBUG:
            frontend_base = settings.cors_origins[0] if settings.cors_origins else "http://localhost:5173"
            print(f"[DEV PASSWORD RESET] {frontend_base}/reset-password?token={reset_token}")


def reset_password_with_token(db: Session, token: str, new_password: str) -> None:
    """Validate reset token and update the user's password."""
    payload = decode_token(token)
    if payload.get("type") != "password_reset" or not payload.get("sub"):
        raise AppException(
            status_code=401,
            detail="Invalid or expired password reset token.",
            code="INVALID_RESET_TOKEN",
        )

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise AppException(
            status_code=401,
            detail="Invalid or expired password reset token.",
            code="INVALID_RESET_TOKEN",
        ) from exc

    validate_password_policy(new_password)

    user = db.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        raise AppException(
            status_code=400,
            detail="Unable to reset password for this account.",
            code="INVALID_RESET_ACCOUNT",
        )

    user.password_hash = hash_password(new_password)
    db.commit()


def change_user_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    """Verify current password, enforce policy, and update password."""
    if not verify_password(current_password, user.password_hash):
        raise AppException(
            status_code=400,
            detail="Current password is incorrect.",
            code="INCORRECT_PASSWORD",
        )
    validate_password_policy(new_password)
    user.password_hash = hash_password(new_password)
    db.commit()


def update_own_profile(
    db: Session,
    user: User,
    full_name: str,
    phone: str | None,
) -> User:
    """Update authenticated user's own profile fields."""
    user.full_name = full_name.strip()
    user.phone = phone.strip() if phone else None
    db.commit()
    db.refresh(user)
    return user
