from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GardenNoteCreate(BaseModel):
    note: str
    garden_id: UUID

    model_config = ConfigDict(from_attributes=True)


class GardenNoteUpdate(BaseModel):
    note: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GardenNoteList(BaseModel):
    id: UUID
    updated_date: datetime
    note: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GardenNoteRead(BaseModel):
    id: UUID
    created_date: datetime
    updated_date: datetime
    note: str | None = None

    model_config = ConfigDict(from_attributes=True)
