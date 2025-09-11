from datetime import datetime, timezone
from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from app.helpers.model_base import ModelBase

if TYPE_CHECKING:
    from app.pages.page_models import Page  # noqa: F401


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    full_name: str | None = None
    is_active: bool = Field(default=True)


class User(ModelBase, UserBase, table=True):  # type: ignore
    hashed_password: str
    roles: List["UserRole"] = Relationship(back_populates="user")
    pages: List["Page"] = Relationship(back_populates="user")


class RoleBase(SQLModel):
    name: str = Field(unique=True, index=True)
    description: str | None = None


class Role(ModelBase, RoleBase, table=True):  # type: ignore
    users: List["UserRole"] = Relationship(back_populates="role")


class UserRole(SQLModel, table=True):  # type: ignore
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    role_id: UUID = Field(foreign_key="role.id", primary_key=True)
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )
    user: User = Relationship(back_populates="roles")
    role: Role = Relationship(back_populates="users")
