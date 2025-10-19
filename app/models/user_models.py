from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlalchemy import String
from sqlmodel import Field, Relationship, SQLModel

from app.models.model_base import ModelBase
from app.models.role_models import Role, UserRoleLink

if TYPE_CHECKING:
    from app.models.garden_models import Garden  # noqa: F401
    from app.models.page_models import Page  # noqa: F401


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: EmailStr = Field(
        sa_type=String,
        unique=True,
        index=True,
        nullable=False,
        description="User email",
    )
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool = Field(default=True)


class User(ModelBase, UserBase, table=True):  # type: ignore
    hashed_password: str
    pages: list["Page"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    gardens: list["Garden"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    roles: list[Role] = Relationship(
        back_populates="users",
        link_model=UserRoleLink,
    )
