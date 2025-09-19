from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlmodel import Field, Relationship

from app.helpers.model_base import ModelBase

if TYPE_CHECKING:
    from app.users.user_models import User  # noqa: F401


class BedNote(ModelBase, table=True):  # type: ignore
    note: str
    bed_id: UUID = Field(foreign_key="bed_id", nullable=False, ondelete="CASCADE")
    bed: "Bed" = Relationship(back_populates="notes")


class Bed(ModelBase, table=True):  # type: ignore
    name: str
    description: str | None = None
    notes: List[BedNote] = Relationship(back_populates="bed")
    garden_id: UUID = Field(
        foreign_key="garden.garden_id", nullable=False, ondelete="CASCADE"
    )
    garden: "Garden" = Relationship(back_populates="beds")


class GardenNote(ModelBase, table=True):  # type: ignore
    note: str
    garden_id: UUID = Field(foreign_key="bed_id", nullable=False, ondelete="CASCADE")
    garden: "Garden" = Relationship(back_populates="notes")


class Garden(ModelBase, table=True):  # type: ignore
    name: str
    description: str | None = None
    location: str = Field(default="Lebanon, Kansas, USA", nullable=False)
    user: "User" = Relationship(back_populates="user")
    is_private: bool = Field(default=True)
    notes: List[GardenNote] = Relationship(back_populates="garden")
    beds: List[Bed] = Relationship(back_populates="beds")
    user_id: UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
