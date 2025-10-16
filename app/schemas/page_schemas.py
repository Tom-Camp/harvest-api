from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PageRead(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    body: str
    created_date: datetime
    updated_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PageList(BaseModel):
    id: UUID
    title: str
    created_date: datetime
    updated_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PageCreate(BaseModel):
    title: str
    body: str

    model_config = ConfigDict(from_attributes=True)


class PageUpdate(BaseModel):
    title: str | None = None
    body: str | None = None

    model_config = ConfigDict(from_attributes=True)
