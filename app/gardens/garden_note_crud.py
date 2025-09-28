import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.gardens.garden_models import GardenNote
from app.gardens.garden_note_schemas import GardenNoteCreate, GardenNoteUpdate
from app.logging import get_logger, log_handler

logger = get_logger(__name__)


class GardenNoteCRUD:

    @staticmethod
    async def create_note(note: GardenNoteCreate, session: AsyncSession) -> GardenNote:
        new_note = GardenNote(**note.model_dump())
        start = time.time()

        session.add(new_note)
        await session.commit()
        await session.refresh(new_note)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_note",
            table="garden_note",
            duration_ms=duration_ms,
            note_id=str(new_note.id),
        )
        return new_note

    @staticmethod
    async def get_note(session: AsyncSession, note_id: UUID) -> GardenNote | None:
        statement = select(GardenNote).where(GardenNote.id == note_id)

        start = time.time()

        result = await session.execute(statement)
        note = result.scalars().first()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_note",
            table="garden_note",
            duration_ms=duration_ms,
            note_id=note_id,
        )
        return note

    @staticmethod
    async def get_notes(
        garden_id: UUID, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[GardenNote]:
        statement = (
            select(GardenNote)
            .where(GardenNote.garden_id == garden_id)
            .offset(skip)
            .limit(limit)
        )

        start = time.time()

        result = await session.execute(statement)
        notes = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_notes",
            table="garden_note",
            duration_ms=duration_ms,
            garden_id=str(garden_id),
        )
        return notes

    @staticmethod
    async def update_note(
        session: AsyncSession, note_id: UUID, note_update: GardenNoteUpdate
    ) -> GardenNote:
        note = await session.get(
            GardenNote, note_id, options=[selectinload(GardenNote.garden)]
        )
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
                table="garden_note",
                duration_ms=duration_ms,
                garden_id=str(note_id),
            )
        return note

    @staticmethod
    async def delete_note(session: AsyncSession, note_id: UUID) -> bool:
        return_value: bool = False

        note = await session.get(GardenNote, note_id)
        if note:
            start = time.time()

            await session.delete(note)
            await session.commit()
            return_value = True

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_note",
                table="garden_note",
                duration_ms=duration_ms,
                note_id=str(note_id),
            )
        return return_value
