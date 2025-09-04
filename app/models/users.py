from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from app.models.model_base import ModelBase


class RoleBase(SQLModel):
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None


class Role(ModelBase, RoleBase, table=True):  # type: ignore
    users: List["UserRole"] = Relationship(back_populates="role")


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
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
