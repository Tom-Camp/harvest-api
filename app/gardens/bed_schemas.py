from typing import List
from uuid import UUID

from pydantic import BaseModel


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
    notes: List[str] | None = None


class BedUpdate(BaseModel):
    name: str
    description: str | None = None
    notes: List[str] | None = None
