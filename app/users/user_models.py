from typing import TYPE_CHECKING, List

from pydantic import EmailStr
from sqlalchemy import String
from sqlmodel import Field, Relationship, SQLModel

from app.helpers.model_base import ModelBase

if TYPE_CHECKING:
    from app.pages.page_models import Page  # noqa: F401


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: EmailStr = Field(
        sa_type=String(320),
        unique=True,
        index=True,
        nullable=False,
        description="User email",
    )
    full_name: str | None = None
    is_active: bool = Field(default=True)


class User(ModelBase, UserBase, table=True):  # type: ignore
    hashed_password: str
    pages: List["Page"] = Relationship(back_populates="user")
