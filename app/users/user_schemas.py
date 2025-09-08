from datetime import datetime
from typing import List
from uuid import UUID

from sqlmodel import SQLModel

from app.helpers.model_base import ModelBase
from app.users.user_models import RoleBase, UserBase


class UserCreate(UserBase):
    password: str


class UserUpdate(SQLModel):
    email: str | None = None
    username: str | None = None
    full_name: str | None = None
    is_active: bool = False


class UserRead(ModelBase, UserBase):
    pass


class UserReadWithRoles(UserRead):
    roles: List["RoleRead"] = []


class RoleCreate(RoleBase):
    pass


class RoleUpdate(SQLModel):
    name: str | None = None
    description: str | None = None


class RoleRead(RoleBase):
    id: UUID
    created_at: datetime


class RoleReadWithUsers(RoleRead):
    users: List["UserRead"] = []
