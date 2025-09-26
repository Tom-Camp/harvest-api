import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.gardens.garden_models import GardenNote
from app.gardens.garden_note_schemas import GardenNoteCreate
from app.logging import get_logger, log_handler

logger = get_logger(__name__)


class GardenNoteCRUD:

    @staticmethod
    async def create_note(note: GardenNoteCreate, session: AsyncSession) -> GardenNote:
        start = time.time()

        new_note = GardenNote(**note.model_dump())
        session.add(new_note)
        await session.commit()
        await session.refresh(new_note)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create garden note",
            table="garden_note",
            duration_ms=duration_ms,
            note_id=str(new_note.id),
        )
        return new_note
