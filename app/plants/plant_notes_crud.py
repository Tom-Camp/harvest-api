import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.logging import get_logger, log_handler
from app.plants.plant_models import PlantNote
from app.plants.plant_notes_schemas import PlantNoteCreate, PlantNoteUpdate

logger = get_logger(__name__)


class PlantNoteCRUD:

    @staticmethod
    async def create_note(note: PlantNoteCreate, session: AsyncSession) -> PlantNote:
        """
        Create a new PlantNote

        :param note: PlantNoteCreate; plants.plant_note_schema.PlantNoteCreate
        :param session: SQLAlchemy asyncio AsyncSession
        :return: PlantNote
        """

        new_note = PlantNote(**note.model_dump())
        start = time.time()

        session.add(new_note)
        await session.commit()
        await session.refresh(new_note)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_note",
            table="plant_note",
            duration_ms=duration_ms,
            note_id=str(new_note.id),
        )
        return new_note

    @staticmethod
    async def get_note(session: AsyncSession, note_id: UUID) -> PlantNote | None:
        """
        Get a PlantNote by ID

        :param session: SQLAlchemy asyncio AsyncSession
        :param note_id: Plant UUID
        :return: PlantNote or None
        """

        statement = select(PlantNote).where(PlantNote.id == note_id)

        start = time.time()

        result = await session.execute(statement)
        note = result.scalars().first()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_note",
            table="plant_note",
            duration_ms=duration_ms,
            note_id=note_id,
        )
        return note

    @staticmethod
    async def get_notes(
        plant_id: UUID, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[PlantNote]:
        """
        Get all PlantNote by the Plant ID

        :param plant_id: Plant UUID
        :param session: SQLAlchemy asyncio AsyncSession
        :param skip: Number of rows to skip
        :param limit: Number of rows to return
        :return: Sequence[PlantNote]
        """
        statement = (
            select(PlantNote)
            .where(PlantNote.plant_id == plant_id)
            .offset(skip)
            .limit(limit)
        )

        start = time.time()

        result = await session.execute(statement)
        notes = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_notes",
            table="plant_note",
            duration_ms=duration_ms,
            garden_id=str(plant_id),
        )
        return notes

    @staticmethod
    async def update_note(
        session: AsyncSession, note_id: UUID, note_update: PlantNoteUpdate
    ) -> PlantNote:
        """
        Update a PlantNote by ID

        :param session: SQLAlchemy asyncio AsyncSession
        :param note_id: Plant UUID
        :param note_update: PlantNoteUpdate
        :return: PlantNote
        """
        note = await session.get(
            PlantNote, note_id, options=[selectinload(PlantNote.plant)]
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
                table="plant_note",
                duration_ms=duration_ms,
                plant_id=str(note.plant_id),
                garden_id=str(note_id),
            )
        return note

    @staticmethod
    async def delete_note(session: AsyncSession, note_id: UUID) -> bool:
        """
        Delete a PlantNote by ID

        :param session: SQLAlchemy asyncio AsyncSession
        :param note_id: Plant UUID
        :return: bool
        """
        return_value: bool = False

        note = await session.get(PlantNote, note_id)
        if note:
            start = time.time()

            await session.delete(note)
            await session.commit()
            return_value = True

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_note",
                table="plant_note",
                duration_ms=duration_ms,
                note_id=str(note_id),
            )
        return return_value
