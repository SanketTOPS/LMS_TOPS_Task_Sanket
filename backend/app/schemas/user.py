from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field


class RoleOut(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    role_id: int
    full_name: str
    email: EmailStr
    phone: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    role: RoleOut | None = Field(default=None, exclude=True)

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def role_name(self) -> str:
        return self.role.name if self.role else ""


class UserCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=1)
    phone: str | None = Field(default=None, max_length=30)
    role_name: Literal["Admin", "Instructor", "Student"]
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    role_name: Literal["Admin", "Instructor", "Student"] | None = None
    is_active: bool | None = None


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=1)


class PaginatedUsersResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
