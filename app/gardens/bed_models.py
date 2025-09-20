from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlmodel import Field, Relationship

from app.helpers.model_base import ModelBase

if TYPE_CHECKING:
    from app.gardens.garden_models import Garden  # noqa: F401


class BedNote(ModelBase, table=True):  # type: ignore
    note: str
    bed_id: UUID = Field(foreign_key="bed.id", nullable=False, ondelete="CASCADE")
    bed: "Bed" = Relationship(back_populates="notes")


class Bed(ModelBase, table=True):  # type: ignore
    name: str
    description: str | None = None
    notes: List[BedNote] = Relationship(back_populates="bed")
    garden_id: UUID = Field(foreign_key="garden.id", nullable=False, ondelete="CASCADE")
    garden: "Garden" = Relationship(back_populates="beds")
