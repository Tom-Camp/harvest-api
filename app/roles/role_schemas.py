from datetime import datetime
from typing import List
from uuid import UUID

from sqlmodel import SQLModel

from app.roles.role_models import RoleBase
from app.users.user_schemas import UserRead


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
