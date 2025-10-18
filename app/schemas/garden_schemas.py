from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.garden_models import GardenNote
from app.schemas.bed_schemas import BedList


class GardenCreate(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None
    is_private: bool = False

    model_config = ConfigDict(from_attributes=True)


class GardenUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None
    is_private: bool = False

    model_config = ConfigDict(from_attributes=True)


class GardenList(BaseModel):
    id: UUID
    created_date: datetime
    updated_date: datetime
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GardenRead(BaseModel):
    id: UUID
    created_date: datetime
    updated_date: datetime
    name: str
    description: str | None = None
    notes: list[GardenNote] | None = None
    beds: list[BedList] | None = None
    is_private: bool

    model_config = ConfigDict(from_attributes=True)
