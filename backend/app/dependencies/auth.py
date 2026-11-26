from collections.abc import Callable, Iterable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.middleware.error_handler import AppException
from app.models.user import User
from app.utils.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Authenticate request via Bearer JWT and return active User with role."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise AppException(
            status_code=401,
            detail="Authentication credentials were not provided.",
            code="NOT_AUTHENTICATED",
        )

    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access" or not payload.get("sub"):
        raise AppException(
            status_code=401,
            detail="Invalid authentication token.",
            code="INVALID_TOKEN",
        )

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise AppException(
            status_code=401,
            detail="Invalid authentication token.",
            code="INVALID_TOKEN",
        ) from exc

    user = db.scalar(
        select(User)
        .options(joinedload(User.role))
        .where(User.id == user_id)
    )
    if not user:
        raise AppException(
            status_code=401,
            detail="User account not found.",
            code="USER_NOT_FOUND",
        )
    if not user.is_active:
        raise AppException(
            status_code=403,
            detail="Account is deactivated.",
            code="INACTIVE_USER",
        )
    return user


def require_role(allowed_roles: Iterable[str]) -> Callable[[User], User]:
    """Return a dependency enforcing that current_user has one of allowed_roles."""
    allowed_set = set(allowed_roles)

    def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_name = current_user.role.name if current_user.role else None
        if role_name not in allowed_set:
            raise AppException(
                status_code=403,
                detail="You do not have permission to perform this action.",
                code="FORBIDDEN",
            )
        return current_user

    return _role_checker
