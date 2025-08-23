from datetime import datetime, timezone

from beanie import (
    Document,
    PydanticObjectId,
    Replace,
    SaveChanges,
    Update,
    before_event,
)
from pydantic import Field


class AutoTimestampedDocument(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @before_event(Replace, Update, SaveChanges)
    def update_updated_date(self):
        self.updated_date = datetime.now(timezone.utc)

    class Settings:
        use_revision = True
