from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.middleware.error_handler import AppException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_policy(password: str) -> None:
    """Enforce password complexity rules from configuration."""
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise AppException(
            status_code=422,
            detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long.",
            code="WEAK_PASSWORD",
        )
    if settings.PASSWORD_REQUIRE_UPPER and not any(ch.isupper() for ch in password):
        raise AppException(
            status_code=422,
            detail="Password must contain at least one uppercase letter.",
            code="WEAK_PASSWORD",
        )
    if settings.PASSWORD_REQUIRE_LOWER and not any(ch.islower() for ch in password):
        raise AppException(
            status_code=422,
            detail="Password must contain at least one lowercase letter.",
            code="WEAK_PASSWORD",
        )
    if settings.PASSWORD_REQUIRE_DIGIT and not any(ch.isdigit() for ch in password):
        raise AppException(
            status_code=422,
            detail="Password must contain at least one digit.",
            code="WEAK_PASSWORD",
        )


def create_access_token(user_id: int, role: str) -> str:
    """Create a signed JWT access token containing user id and role."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_reset_token(user_id: int) -> str:
    """Create a short-lived signed JWT token for password reset."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "password_reset",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token, raising AppException on failure."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise AppException(
            status_code=401,
            detail="Invalid or expired token.",
            code="INVALID_TOKEN",
        ) from exc
