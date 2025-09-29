from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.beds.bed_models import BedNote


class BedCreate(BaseModel):
    name: str
    description: str | None = None
    garden_id: UUID

    model_config = ConfigDict(from_attributes=True)


class BedList(BaseModel):
    id: UUID
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BedRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    notes: list[BedNote] | None = None

    model_config = ConfigDict(from_attributes=True)


class BedUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    notes: list[BedNote] | None = None

    model_config = ConfigDict(from_attributes=True)
