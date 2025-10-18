import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.logging import get_logger, log_handler
from app.models.bed_models import BedNote
from app.schemas.bed_notes_schemas import BedNoteCreate, BedNoteUpdate

logger = get_logger(__name__)


class BedNoteService:

    def __init__(self, session: AsyncSession):
        self._db = session

    async def create_note(self, note: BedNoteCreate) -> BedNote:
        """
        Create a new BedNote

        :param note: BedNoteCreate; beds.bed_note_schema.BedNoteCreate
        :return: BedNote
        """

        new_note = BedNote(**note.model_dump())
        start = time.time()

        self._db.add(new_note)
        await self._db.commit()
        await self._db.refresh(new_note)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_note",
            table="bed_note",
            duration_ms=duration_ms,
            note_id=str(new_note.id),
        )
        return new_note

    async def get_note(self, note_id: UUID) -> BedNote | None:
        """
        Get a BedNote by ID

        :param note_id: Bed UUID
        :return: BedNote or None
        """

        statement = select(BedNote).where(BedNote.id == note_id)

        start = time.time()

        result = await self._db.execute(statement)
        note = result.scalars().first()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_note",
            table="bed_note",
            duration_ms=duration_ms,
            note_id=note_id,
        )
        return note

    async def get_notes(
        self, bed_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[BedNote | None]:
        """
        Get all BedNotes by the Bed ID

        :param bed_id: Bed UUID
        :param skip: Number of rows to skip
        :param limit: Number of rows to return
        :return: Sequence[BedNote | None]
        """
        statement = (
            select(BedNote).where(BedNote.bed_id == bed_id).offset(skip).limit(limit)
        )

        start = time.time()

        result = await self._db.execute(statement)
        notes = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_notes",
            table="bed_note",
            duration_ms=duration_ms,
            garden_id=str(bed_id),
        )
        return notes

    async def update_note(
        self, note_id: UUID, note_update: BedNoteUpdate
    ) -> BedNote | None:
        """
        Update a BedNote by ID

        :param note_id: Bed UUID
        :param note_update: BedNoteUpdate
        :return: BedNote
        """
        note = await self._db.get(BedNote, note_id, options=[selectinload(BedNote.bed)])
        if note:
            note_data = note_update.model_dump(exclude_unset=True)
            for field, value in note_data.items():
                setattr(note, field, value)
            start = time.time()

            self._db.add(note)
            await self._db.commit()
            await self._db.refresh(note)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_note",
                table="bed_note",
                duration_ms=duration_ms,
                bed_id=str(note.bed_id),
                garden_id=str(note_id),
            )
        return note

    async def delete_note(self, note_id: UUID) -> bool:
        """
        Delete a BedNote by ID

        :param note_id: Bed UUID
        :return: bool
        """
        return_value: bool = False

        note = await self._db.get(BedNote, note_id)
        if note:
            start = time.time()

            await self._db.delete(note)
            await self._db.commit()
            return_value = True

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_note",
                table="bed_note",
                duration_ms=duration_ms,
                note_id=str(note_id),
            )
        return return_value
