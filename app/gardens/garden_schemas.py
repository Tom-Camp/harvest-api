from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.beds.bed_schemas import BedRead
from app.gardens.garden_models import GardenNote


class GardenCreate(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None
    is_private: bool = False


class GardenUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None
    is_private: bool = False


class GardenList(BaseModel):
    id: UUID
    created_date: datetime
    updated_date: datetime
    name: str
    description: str | None = None


class GardenRead(BaseModel):
    id: UUID
    created_date: datetime
    updated_date: datetime
    name: str
    description: str | None = None
    notes: list[GardenNote] | None = None
    beds: list[BedRead] | None = None
    is_private: bool
