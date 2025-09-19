from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from app.helpers.model_base import ModelBase

if TYPE_CHECKING:
    from app.users.user_models import User  # noqa: F401


class Page(ModelBase, table=True):  # type: ignore
    title: str
    body: str
    user_id: UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    user: "User" = Relationship(back_populates="pages")
