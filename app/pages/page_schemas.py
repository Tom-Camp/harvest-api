from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class PageRead(SQLModel):
    id: UUID
    user_id: UUID
    title: str
    body: str
    created_date: datetime


class PageList(SQLModel):
    id: UUID
    user_id: UUID
    title: str
    created_date: datetime
