from pydantic import Field

from app.helpers.model_base import ModelBase


class Note(ModelBase):
    note: str = Field(description="A simple note")
