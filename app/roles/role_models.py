from typing import List

from sqlmodel import Field, Relationship, SQLModel

from app.helpers.model_base import ModelBase
from app.users.user_models import UserRole


class RoleBase(SQLModel):
    name: str = Field(unique=True, index=True)
    description: str | None = None


class Role(ModelBase, RoleBase, table=True):  # type: ignore
    users: List["UserRole"] = Relationship(back_populates="role")
