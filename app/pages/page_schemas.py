from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PageRead(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    body: str
    created_date: datetime


class PageList(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    created_date: datetime


class PageCreate(BaseModel):
    title: str
    body: str


class PageUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
