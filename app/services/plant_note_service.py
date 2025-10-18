import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.logging import get_logger, log_handler
from app.models.plant_models import PlantNote
from app.schemas.plant_notes_schemas import PlantNoteCreate, PlantNoteUpdate

logger = get_logger(__name__)


class PlantNoteService:

    def __init__(self, session: AsyncSession):
        self._db = session

    async def create_note(self, note: PlantNoteCreate) -> PlantNote:
        """
        Create a new PlantNote

        :param note: PlantNoteCreate; plants.plant_note_schema.PlantNoteCreate
        :return: PlantNote
        """

        new_note = PlantNote(**note.model_dump())
        start = time.time()

        self._db.add(new_note)
        await self._db.commit()
        await self._db.refresh(new_note)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_note",
            table="plant_note",
            duration_ms=duration_ms,
            note_id=str(new_note.id),
        )
        return new_note

    async def get_note(self, note_id: UUID) -> PlantNote | None:
        """
        Get a PlantNote by ID

        :param note_id: Plant UUID
        :return: PlantNote or None
        """

        statement = select(PlantNote).where(PlantNote.id == note_id)

        start = time.time()

        result = await self._db.execute(statement)
        note = result.scalars().first()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_note",
            table="plant_note",
            duration_ms=duration_ms,
            note_id=note_id,
        )
        return note

    async def get_notes(
        self, plant_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[PlantNote]:
        """
        Get all PlantNote by the Plant ID

        :param plant_id: Plant UUID
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

        result = await self._db.execute(statement)
        notes = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_notes",
            table="plant_note",
            duration_ms=duration_ms,
            garden_id=str(plant_id),
        )
        return notes

    async def update_note(
        self, note_id: UUID, note_update: PlantNoteUpdate
    ) -> PlantNote:
        """
        Update a PlantNote by ID

        :param note_id: Plant UUID
        :param note_update: PlantNoteUpdate
        :return: PlantNote
        """
        note = await self._db.get(
            PlantNote, note_id, options=[selectinload(PlantNote.plant)]
        )
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
                table="plant_note",
                duration_ms=duration_ms,
                plant_id=str(note.plant_id),
                garden_id=str(note_id),
            )
        return note

    async def delete_note(self, note_id: UUID) -> bool:
        """
        Delete a PlantNote by ID

        :param note_id: Plant UUID
        :return: bool
        """
        return_value: bool = False

        note = await self._db.get(PlantNote, note_id)
        if note:
            start = time.time()

            await self._db.delete(note)
            await self._db.commit()
            return_value = True

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_note",
                table="plant_note",
                duration_ms=duration_ms,
                note_id=str(note_id),
            )
        return return_value
