import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.logging import get_logger, log_handler
from app.plants.plant_models import PlantNote
from app.plants.plant_notes_schemas import PlantNoteCreate

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
        :param note_id: Bed UUID
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
