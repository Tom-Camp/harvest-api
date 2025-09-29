from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BedNoteCreate(BaseModel):
    note: str
    bed_id: UUID

    model_config = ConfigDict(from_attributes=True)


class BedNoteUpdate(BaseModel):
    note: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BedNoteList(BaseModel):
    id: UUID
    updated_date: datetime
    note: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BedNoteRead(BaseModel):
    id: UUID
    created_date: datetime
    updated_date: datetime
    note: str | None = None

    model_config = ConfigDict(from_attributes=True)
