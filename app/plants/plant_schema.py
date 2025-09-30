from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.plants.plant_models import Harvest, PlantNote
from app.plants.recommendation_schema import RecommendationRead


class PlantCreate(BaseModel):
    species: str
    variety: str | None = None
    germination_date: datetime | None = None
    planted_date: datetime | None = None
    bed_id: UUID

    model_config = ConfigDict(from_attributes=True)


class PlantUpdate(BaseModel):
    species: str
    variety: str | None = None
    germination_date: datetime | None = None
    planted_date: datetime | None = None
    bed_id: UUID

    model_config = ConfigDict(from_attributes=True)


class PlantList(BaseModel):
    species: str
    variety: str | None = None
    planted_date: datetime | None = None
    bed_id: UUID

    model_config = ConfigDict(from_attributes=True)


class PlantRead(BaseModel):
    id: UUID
    species: str
    variety: str | None = None
    bed_id: UUID
    germination_date: datetime | None = None
    planted_date: datetime | None = None
    recommendations: RecommendationRead
    harvest: list[Harvest] | None = None
    notes: list[PlantNote] | None = None

    model_config = ConfigDict(from_attributes=True)
