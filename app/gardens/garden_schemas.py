from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel

from app.gardens.bed_schemas import BedRead


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
    notes: List[str] | None = None
    bed_ids: List[BedRead] | None = None
    is_private: bool
