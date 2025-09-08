from datetime import datetime, timezone
from typing import List
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from app.helpers.model_base import ModelBase
from app.roles.role_models import Role


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    full_name: str | None = None
    is_active: bool = Field(default=True)


class User(ModelBase, UserBase, table=True):  # type: ignore
    hashed_password: str
    roles: List["UserRole"] = Relationship(back_populates="user")


class UserRole(SQLModel, table=True):  # type: ignore
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    role_id: UUID = Field(foreign_key="role.id", primary_key=True)
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )
    user: User = Relationship(back_populates="roles")
    role: Role = Relationship(back_populates="users")
