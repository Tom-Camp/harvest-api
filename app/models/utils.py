from pydantic import Field

from app.models.base import AutoTimestampedDocument


class Note(AutoTimestampedDocument):
    note: str = Field(description="A simple note")
