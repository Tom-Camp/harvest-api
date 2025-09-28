import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.beds.bed_models import BedNote
from app.beds.bed_note_schemas import BedNoteCreate
from app.logging import get_logger, log_handler

logger = get_logger(__name__)


class BedNoteCRUD:

    @staticmethod
    async def create_note(note: BedNoteCreate, session: AsyncSession) -> BedNote:
        new_note = BedNote(**note.model_dump())
        start = time.time()

        session.add(new_note)
        await session.commit()
        await session.refresh(new_note)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_note",
            table="bed_note",
            duration_ms=duration_ms,
            note_id=str(new_note.id),
        )
        return new_note

    @staticmethod
    async def get_note(session: AsyncSession, note_id: UUID) -> BedNote | None:
        statement = select(BedNote).where(BedNote.id == note_id)

        start = time.time()

        result = await session.execute(statement)
        note = result.scalars().first()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_note",
            table="bed_note",
            duration_ms=duration_ms,
            note_id=note_id,
        )
        return note

    @staticmethod
    async def get_notes(
        bed_id: UUID, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[BedNote]:
        statement = (
            select(BedNote).where(BedNote.bed_id == bed_id).offset(skip).limit(limit)
        )

        start = time.time()

        result = await session.execute(statement)
        notes = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_notes",
            table="bed_note",
            duration_ms=duration_ms,
            garden_id=str(bed_id),
        )
        return notes
