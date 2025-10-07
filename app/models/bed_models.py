from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.model_base import ModelBase
from app.models.plant_models import Plant

if TYPE_CHECKING:
    from app.models.garden_models import Garden  # noqa: F401


class BedNote(ModelBase, table=True):  # type: ignore
    note: str
    bed_id: UUID = Field(foreign_key="bed.id", nullable=False, ondelete="CASCADE")
    bed: "Bed" = Relationship(back_populates="notes")


class Bed(ModelBase, table=True):  # type: ignore
    name: str
    description: str | None = None
    notes: list[BedNote] = Relationship(
        back_populates="bed",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    plants: list[Plant] = Relationship(
        back_populates="bed",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    garden_id: UUID = Field(foreign_key="garden.id", nullable=False, ondelete="CASCADE")
    garden: "Garden" = Relationship(back_populates="beds")
