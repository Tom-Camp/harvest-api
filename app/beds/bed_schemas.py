from uuid import UUID

from pydantic import BaseModel

from app.beds.bed_models import BedNote


class BedCreate(BaseModel):
    name: str
    description: str | None = None
    garden_id: UUID


class BedList(BaseModel):
    name: str
    description: str | None = None
    garden_id: UUID


class BedRead(BaseModel):
    name: str
    description: str | None = None
    notes: list[BedNote] | None = None


class BedUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    notes: list[BedNote] | None = None
