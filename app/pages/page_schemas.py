from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.pages.page_models import PageBase


class PageCreate(PageBase):
    pass


class PageUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PageRead(PageBase):
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
