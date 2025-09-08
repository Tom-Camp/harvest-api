from uuid import UUID

from sqlmodel import Field, SQLModel

from app.helpers.model_base import ModelBase


class PageBase(SQLModel):
    title: str
    body: str


class Page(ModelBase, PageBase, table=True):  # type: ignore
    owner_id: UUID = Field(foreign_key="user.id")
