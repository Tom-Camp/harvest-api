import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.beds.bed_models import BedNote
from app.beds.bed_note_schemas import BedNoteCreate, BedNoteUpdate
from app.logging import get_logger, log_handler

logger = get_logger(__name__)


class BedNoteCRUD:

    @staticmethod
    async def create_note(note: BedNoteCreate, session: AsyncSession) -> BedNote:
        """
        Create a new BedNote

        :param note: BedNoteCreate; beds/bednote_schema.py
        :param session: SQLAlchemy asyncio AsyncSession
        :return: BedNote
        """

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
        """
        Get a BedNote by ID

        :param session: SQLAlchemy asyncio AsyncSession
        :param note_id: Bed UUID
        :return: BedNote or None
        """

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
        """
        Get all BedNotes by the Bed ID

        :param bed_id: Bed UUID
        :param session: SQLAlchemy asyncio AsyncSession
        :param skip: Number of rows to skip
        :param limit: Number of rows to return
        :return: Sequence[BedNote]
        """
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

    @staticmethod
    async def update_note(
        session: AsyncSession, note_id: UUID, note_update: BedNoteUpdate
    ) -> BedNote:
        """
        Update a BedNote by ID

        :param session: SQLAlchemy asyncio AsyncSession
        :param note_id: Bed UUID
        :param note_update: BedNoteUpdate
        :return: BedNote
        """
        note = await session.get(BedNote, note_id, options=[selectinload(BedNote.bed)])
        if note:
            note_data = note_update.model_dump(exclude_unset=True)
            for field, value in note_data.items():
                setattr(note, field, value)
            start = time.time()

            session.add(note)
            await session.commit()
            await session.refresh(note)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_note",
                table="bed_note",
                duration_ms=duration_ms,
                bed_id=str(note.bed_id),
                garden_id=str(note_id),
            )
        return note

    @staticmethod
    async def delete_note(session: AsyncSession, note_id: UUID) -> bool:
        """
        Delete a BedNote by ID

        :param session: SQLAlchemy asyncio AsyncSession
        :param note_id: Bed UUID
        :return: bool
        """
        return_value: bool = False

        note = await session.get(BedNote, note_id)
        if note:
            start = time.time()

            await session.delete(note)
            await session.commit()
            return_value = True

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_note",
                table="bed_note",
                duration_ms=duration_ms,
                note_id=str(note_id),
            )
        return return_value
