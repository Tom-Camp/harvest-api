from typing import List

from pydantic import BaseModel

from app.gardens.bed_schemas import BedRead


class GardenCreate(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None


class GardenList(BaseModel):
    name: str
    description: str | None = None


class GardenRead(BaseModel):
    name: str
    description: str | None = None
    notes: List[str] | None = None
    bed_ids: List[BedRead] | None = None
    is_private: bool


class GardenUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None
    notes: List[str] | None = None
    is_private: bool
