from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.model_base import ModelBase

if TYPE_CHECKING:
    from app.plants.plant_models import Plant


class LifeCycle(str, Enum):
    PERENNIAL = "perennial"
    ANNUAL = "annual"
    BIENNIAL = "biennial"


class PlantingWindow(ModelBase, table=True):  # type: ignore
    season: str | None = Field(
        description="Growing season (spring, summer, fall, winter)"
    )
    months: str | None = Field(
        description="A comma separated list of months for planting"
    )
    temperature_range: str | None = Field(description="Ideal soil temperature range")
    recommendations_id: UUID = Field(
        foreign_key="recommendations.id", nullable=False, ondelete="CASCADE"
    )
    recommendations: "Recommendations" = Relationship(back_populates="planting_window")

    class Settings:
        name = "planting_window"


class CareInstructions(ModelBase, table=True):  # type: ignore
    watering_frequency: str | None = Field(description="How often to water")
    sunlight_needs: str | None = Field(description="Sun exposure requirements")
    soil_type: str | None = Field(description="Preferred soil conditions")
    spacing: str | None = Field(description="Recommended plant spacing")
    recommendations_id: UUID = Field(
        foreign_key="recommendations.id", nullable=False, ondelete="CASCADE"
    )
    recommendations: "Recommendations" = Relationship(
        back_populates="care_instructions"
    )

    class Settings:
        name = "care_instructions"


class GrowingTips(ModelBase, table=True):  # type: ignore
    tips: str
    recommendations_id: UUID = Field(
        foreign_key="recommendations.id", nullable=False, ondelete="CASCADE"
    )
    recommendations: "Recommendations" = Relationship(back_populates="growing_tips")


class Pest(ModelBase, table=True):  # type: ignore
    pest: str
    recommendations_id: UUID = Field(
        foreign_key="recommendations.id", nullable=False, ondelete="CASCADE"
    )
    recommendations: "Recommendations" = Relationship(back_populates="pests")


class Recommendations(ModelBase, table=True):  # type: ignore
    life_cycle: LifeCycle | None = Field(description="Perennial, annual, or biennial")
    days_to_harvest: int | None = Field(
        description="Days from seed to harvest", default=None
    )
    companion_plants: str | None = Field(
        description="A comma separated list of plants that support this plant"
    )
    growing_tips: list[GrowingTips] | None = Relationship(
        back_populates="recommendations",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    planting_window: PlantingWindow = Relationship(
        back_populates="recommendations",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    care_instructions: CareInstructions = Relationship(
        back_populates="recommendations",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    pests: list[Pest] = Relationship(
        back_populates="recommendations",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    plant_id: UUID = Field(foreign_key="plant.id", nullable=False, ondelete="CASCADE")
    plant: "Plant" = Relationship(back_populates="recommendations")

    class Settings:
        name = "recommendations"
