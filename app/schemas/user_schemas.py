from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.models.users import RoleBase, UserBase


class UserCreate(UserBase):
    password: str


class UserUpdate(SQLModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: str
    created_date: datetime
    updated_date: datetime


class UserReadWithRoles(UserRead):
    roles: List["RoleRead"] = []


class RoleCreate(RoleBase):
    pass


class RoleUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleRead(RoleBase):
    id: UUID
    created_at: datetime


class RoleReadWithUsers(RoleRead):
    users: List["UserRead"] = []
