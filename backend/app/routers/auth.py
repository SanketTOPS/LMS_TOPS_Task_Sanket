from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ProfileUpdateRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services import auth_service
from app.utils.limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user with email & password and issue a JWT."""
    token, user = auth_service.authenticate_user(db, payload.email, payload.password)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("5/minute")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Initiate password reset; prints reset link to console in development."""
    auth_service.initiate_password_reset(db, payload.email)
    return MessageResponse(
        detail="If an active account with that email exists, a password reset link has been generated."
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Reset password using a valid time-limited reset token."""
    auth_service.reset_password_with_token(db, payload.token, payload.new_password)
    return MessageResponse(detail="Password has been reset successfully.")


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Change the authenticated user's password."""
    auth_service.change_user_password(
        db, current_user, payload.current_password, payload.new_password
    )
    return MessageResponse(detail="Password changed successfully.")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_me(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update the authenticated user's profile details."""
    updated = auth_service.update_own_profile(
        db, current_user, payload.full_name, payload.phone
    )
    return UserResponse.model_validate(updated)
