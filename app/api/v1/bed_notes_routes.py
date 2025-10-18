from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.auth.auth import get_current_user
from app.core.utils.database import AsyncSessionLocal, get_db
from app.core.utils.garden_helpers import check_garden_access
from app.logging import get_logger, log_handler
from app.models.bed_models import Bed, BedNote
from app.models.garden_models import Garden
from app.schemas.auth_schemas import TokenData
from app.schemas.bed_notes_schemas import (
    BedNoteCreate,
    BedNoteList,
    BedNoteRead,
    BedNoteUpdate,
)
from app.services.bed_note_service import BedNoteService

logger = get_logger(__name__)

bed_note_router = APIRouter(prefix="/bed-notes")


def get_bed_note_service() -> BedNoteService:
    return BedNoteService(session=AsyncSessionLocal())


@bed_note_router.post("/", response_model=BedNote)
async def create_bed_note(
    note: BedNoteCreate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: BedNoteService = Depends(get_bed_note_service),
    session: AsyncSession = Depends(get_db),
) -> BedNote:
    """
    Route for creating a bed note.

    :param note: BedNoteCreate; schemas.bed_note_schemas.BedNoteCreate
    :param current_user: User
    :param service: services.bed_note_service.BedNoteService
    :param session: SQLAlchemy AsyncSession
    :return: BedNote
    """

    statement = (
        select(Garden.user_id, Garden.id, Bed.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .where(Bed.id == note.bed_id)
    )
    result = await session.execute(statement)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    garden_user, garden_id, bed_id = row

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:up"
    )

    new_note = await service.create_note(note=note)
    log_handler.log_garden_event(
        event="Create Note",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": garden_id,
            "bed": new_note.bed_id,
            "note_id": new_note.id,
            "action": "create_bed_note",
            "resource": "bed_note_routes",
        },
    )

    return new_note


@bed_note_router.get("/{note_id}", response_model=BedNoteRead)
async def read_bed_note(
    note_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    service: BedNoteService = Depends(get_bed_note_service),
    session: AsyncSession = Depends(get_db),
) -> BedNote:
    """
    Route for getting a bed note.

    :param note_id: UUID
    :param current_user: User
    :param service: services.bed_note_service.BedNoteService
    :param session: SQLAlchemy AsyncSession
    :return: BedNoteRead; schems.bed_note_schemas.BedNoteRead
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    statement = (
        select(Garden.user_id, Garden.id, Bed.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .where(Bed.id == note.bed_id)
    )
    result = await session.execute(statement)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    garden_user, garden_id, bed_id = row

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:re"
    )

    return note


@bed_note_router.get("/notes/{bed_id}", response_model=list[BedNoteList])
async def read_bed_notes(
    bed_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    skip: int = 0,
    limit: int = 100,
    service: BedNoteService = Depends(get_bed_note_service),
    session: AsyncSession = Depends(get_db),
) -> list[BedNoteList]:
    """
    Route for getting a list of bed notes.

    :param bed_id: UUID
    :param skip: number of rows to skip
    :param limit: limit number of rows to return
    :param service: services.bed_note_service.BedNoteService
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    """

    statement = (
        select(Garden.user_id, Garden.id, Bed.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .where(Bed.id == bed_id)
    )
    result = await session.execute(statement)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    garden_user, garden_id, bed_id = row

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:re"
    )

    notes = await service.get_notes(
        bed_id=bed_id,
        skip=skip,
        limit=limit,
    )
    return [BedNoteList.model_validate(note) for note in notes]


@bed_note_router.put("/{note_id}", response_model=BedNote)
async def update_bed_note(
    note_id: UUID,
    note_update: BedNoteUpdate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: BedNoteService = Depends(get_bed_note_service),
    session: AsyncSession = Depends(get_db),
) -> BedNote | None:
    """
    Route for updating a bed note.

    :param note_id: UUID
    :param note_update: BedNoteUpdate object; schemas.bed_note_schemas.BedNoteUpdate
    :param service: services.bed_note_service.BedNoteService
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: BedNote
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    statement = (
        select(Garden.user_id, Garden.id, Bed.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .where(Bed.id == note.bed_id)
    )
    result = await session.execute(statement)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    garden_user, garden_id, bed_id = row

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:up"
    )

    updated_note = await service.update_note(
        note_id=note_id,
        note_update=note_update,
    )
    if updated_note:
        log_handler.log_garden_event(
            event="Update BedNote",
            context={
                "actor_id": current_user.id,
                "actor_username": current_user.username,
                "garden_id": garden_id,
                "bed_id": updated_note.bed_id,
                "note_id": updated_note.id,
                "action": "update_bed_note",
                "resource": "bed_note_routes",
            },
        )
    return updated_note


@bed_note_router.delete("/{note_id}")
async def delete_bed_note(
    note_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: BedNoteService = Depends(get_bed_note_service),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Route to delete bed note.

    :param note_id: UUID
    :param service: services.bed_note_service.BedNoteService
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: dict
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    statement = (
        select(Garden.user_id, Garden.id, Bed.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .where(Bed.id == note.bed_id)
    )
    result = await session.execute(statement)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    garden_user, garden_id, bed_id = row

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:up"
    )

    if not await service.delete_note(note_id=note_id):
        raise HTTPException(status_code=404, detail="Note not found")

    log_handler.log_garden_event(
        event="Delete BedNote",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": garden_id,
            "bed_id": bed_id,
            "note_id": note.id,
            "action": "delete_bed_note",
            "resource": "bed_note_routes",
        },
    )

    return {"message": "Note deleted successfully"}
