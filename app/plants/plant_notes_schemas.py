from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlantNoteCreate(BaseModel):
    note: str
    plant_id: UUID

    model_config = ConfigDict(from_attributes=True)


class PlantNoteRead(BaseModel):
    id: UUID
    created_date: datetime
    updated_date: datetime
    note: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PlantNoteUpdate(BaseModel):
    note: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PlantNoteList(BaseModel):
    id: UUID
    updated_date: datetime
    note: str | None = None

    model_config = ConfigDict(from_attributes=True)
