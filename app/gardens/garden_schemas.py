from typing import List

from pydantic import BaseModel


class BedList(BaseModel):
    name: str
    description: str | None = None


class BedRead(BaseModel):
    name: str
    description: str | None = None
    notes: List[str] | None = None


class BedUpdate(BaseModel):
    name: str
    description: str | None = None
    notes: List[str] | None = None


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
    name: str
    description: str | None = None
    location: str
    notes: List[str] | None = None
    is_private: bool
