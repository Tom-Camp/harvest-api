from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from app.models.helper_models import Note
from app.models.model_base import ModelBase
from app.models.users import User


class LifeCycle(str, Enum):
    PERENNIAL = "perennial"
    ANNUAL = "annual"


class PlantingWindow(BaseModel):
    season: str = Field(description="Growing season (spring, summer, fall, winter)")
    months: List[str] = Field(description="Specific months for planting")
    temperature_range: str = Field(description="Ideal soil temperature range")

    class Settings:
        name = "planting_window"


class CareInstructions(ModelBase):
    watering_frequency: str = Field(description="How often to water")
    sunlight_needs: str = Field(description="Sun exposure requirements")
    soil_type: str = Field(description="Preferred soil conditions")
    spacing: str = Field(description="Recommended plant spacing")


class PlantInfo(ModelBase):
    planting_window: PlantingWindow
    care_instructions: CareInstructions
    days_to_harvest: int | None = Field(
        description="Days from seed to harvest", default=None
    )
    companion_plants: List[str] = Field(
        description="Plants that grow well together", default=[]
    )
    growing_tips: List[str] = Field(description="Additional growing advice", default=[])


class Harvest(ModelBase, table=True):  # type: ignore
    weight: float


class Plant(ModelBase, table=True):  # type: ignore
    species: str = Field(description="Plant type or family")
    variety: str | None = Field(
        description="The plant variety, for example Roma tomato", default=None
    )
    life_cycle: LifeCycle = Field(description="Perennial or annual")
    germination_date: datetime | None = Field(
        description="The date that germination was begun", default=None
    )
    planting: datetime | None = Field(
        description="The date the sprout was planted", default=None
    )
    notes: List[Note] | None = Field(description="Notes about this plant", default=None)
    harvest: List[Harvest] | None = None
    recommendations: PlantInfo | None = None


class PlantCreate(Plant):
    pass


class Bed(ModelBase, table=True):  # type: ignore
    name: str
    description: str | None = None
    plants: List[Plant] | None = None


class Garden(ModelBase, table=True):  # type: ignore
    name: str
    user: User
    description: str | None = None
    location: str = Field(
        description="The location from which to determine the USDA zone."
    )
    zone: str | None = Field(description="USDA Plant Hardiness Zone", default=None)
    beds: List[Bed] | None = None


class GardenList(Garden):
    pass


class GardenCreate(Garden):
    pass


class GardenUpdate(Garden):
    pass
