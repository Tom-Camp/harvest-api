from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BedNoteCreate(BaseModel):
    note: str
    bed_id: UUID


class BedNoteUpdate(BaseModel):
    note: str | None = None


class BedNoteList(BaseModel):
    id: UUID
    created_date: datetime
    updated_date: datetime
    note: str | None = None


class BedNoteRead(BaseModel):
    id: UUID
    created_date: datetime
    updated_date: datetime
    note: str | None = None
