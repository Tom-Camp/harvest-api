from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from app.models.model_base import ModelBase

if TYPE_CHECKING:
    from app.models.user_models import User  # noqa: F401


class UserRoleLink(SQLModel, table=True):  # type: ignore
    user_id: UUID | None = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: UUID | None = Field(default=None, foreign_key="role.id", primary_key=True)


class Role(ModelBase, table=True):  # type: ignore
    name: str = Field(index=True)
    description: str | None = None
    users: list["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)
