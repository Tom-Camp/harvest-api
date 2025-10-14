from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.model_base import ModelBase

if TYPE_CHECKING:
    from app.beds.bed_models import Bed  # noqa: F401
    from app.users.user_models import User  # noqa: F401


class GardenNote(ModelBase, table=True):  # type: ignore
    note: str
    garden_id: UUID = Field(foreign_key="garden.id", nullable=False, ondelete="CASCADE")
    garden: "Garden" = Relationship(back_populates="notes")


class Garden(ModelBase, table=True):  # type: ignore
    name: str = Field(default="Default Garden", nullable=False)
    description: str | None = None
    location: str = Field(default="Lebanon, Kansas, USA", nullable=False)
    is_private: bool = Field(default=True)
    notes: list[GardenNote] = Relationship(
        back_populates="garden", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    beds: list["Bed"] = Relationship(
        back_populates="garden", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    user_id: UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    user: "User" = Relationship(back_populates="gardens")
