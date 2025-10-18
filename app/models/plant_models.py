from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.model_base import ModelBase
from app.models.recommendation_model import Recommendations

if TYPE_CHECKING:
    from app.models.bed_models import Bed  # noqa: F401# noqa: F401


class PlantNote(ModelBase, table=True):  # type: ignore
    note: str
    plant_id: UUID = Field(foreign_key="plant.id", nullable=False, ondelete="CASCADE")
    plant: "Plant" = Relationship(back_populates="notes")


class Harvest(ModelBase, table=True):  # type: ignore
    weight: float
    plant_id: UUID = Field(foreign_key="plant.id", nullable=False, ondelete="CASCADE")
    plant: "Plant" = Relationship(back_populates="harvest")


class Plant(ModelBase, table=True):  # type: ignore
    species: str = Field(description="Plant type or family")
    variety: str | None = Field(
        description="The plant variety, for example Roma tomato", default=None
    )
    germination_date: datetime | None = Field(
        description="The date that germination was begun", default=None
    )
    planted_date: datetime | None = Field(
        description="The date the sprout was planted", default=None
    )
    notes: list[PlantNote] | None = Relationship(
        back_populates="plant",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    recommendations: Recommendations | None = Relationship(
        back_populates="plant",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    harvest: list[Harvest] | None = Relationship(
        back_populates="plant",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    bed_id: UUID = Field(foreign_key="bed.id", nullable=False, ondelete="CASCADE")
    bed: "Bed" = Relationship(back_populates="plants")
