import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class ModelBase(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )
    updated_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )

    def update_timestamp(self):
        self.updated_date = datetime.now(timezone.utc).replace(tzinfo=None)
