from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GardenNoteCreate(BaseModel):
    note: str
    garden_id: UUID


class GardenNoteUpdate(BaseModel):
    note: str | None = None


class GardenNoteList(BaseModel):
    id: UUID
    created_date: datetime
    updated_date: datetime
    note: str | None = None


class GardenNoteRead(BaseModel):
    id: UUID
    created_date: datetime
    updated_date: datetime
    note: str | None = None
