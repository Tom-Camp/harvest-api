from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_user
from app.auth.auth_schemas import TokenData
from app.beds.bed_crud import BedCRUD
from app.beds.bed_models import BedNote
from app.beds.bed_notes_crud import BedNoteCRUD
from app.beds.bed_notes_schemas import (
    BedNoteCreate,
    BedNoteList,
    BedNoteRead,
    BedNoteUpdate,
)
from app.core.utils.garden_access import check_garden_access
from app.gardens.garden_crud import GardenCRUD
from app.logging import get_logger, log_handler
from app.utils.database import get_db

logger = get_logger(__name__)

bed_note_router = APIRouter(prefix="/bed-notes")


@bed_note_router.post("/", response_model=BedNote)
async def create_bed_note(
    note: BedNoteCreate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    session: AsyncSession = Depends(get_db),
) -> BedNote:
    """
    Route for creating a bed note.

    :param note: BedNoteCreate; beds.bed_note_schemas.BedNoteCreate
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: BedNote
    """

    bed = await BedCRUD.get_bed(session=session, bed_id=note.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:up"
    )

    new_note = await BedNoteCRUD.create_note(
        note=note,
        session=session,
    )
    log_handler.log_garden_event(
        event="Create Note",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": garden.id,
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
    session: AsyncSession = Depends(get_db),
) -> BedNote:
    """
    Route for getting a bed note.

    :param note_id: UUID
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: BedNoteRead; beds.bed_note_schemas.BedNoteRead
    """

    note = await BedNoteCRUD.get_note(note_id=note_id, session=session)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    bed = await BedCRUD.get_bed(session=session, bed_id=note.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:re"
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
    session: AsyncSession = Depends(get_db),
) -> list[BedNoteList]:
    """
    Route for getting a list of bed notes.

    :param bed_id: UUID
    :param skip: number of rows to skip
    :param limit: limit number of rows to return
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    """

    bed = await BedCRUD.get_bed(session=session, bed_id=bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:re"
    )

    notes = await BedNoteCRUD.get_notes(
        bed_id=bed_id,
        session=session,
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
    session: AsyncSession = Depends(get_db),
) -> BedNote:
    """
    Route for updating a bed note.

    :param note_id: UUID
    :param note_update: BedNoteUpdate object; beds.bed_note_schemas.BedNoteUpdate
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: BedNote
    """

    note = await BedNoteCRUD.get_note(note_id=note_id, session=session)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    bed = await BedCRUD.get_bed(session=session, bed_id=note.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:re"
    )

    updated_note = await BedNoteCRUD.update_note(
        session=session,
        note_id=note_id,
        note_update=note_update,
    )
    if updated_note:
        log_handler.log_garden_event(
            event="Update BedNote",
            context={
                "actor_id": current_user.id,
                "actor_username": current_user.username,
                "garden_id": garden.id,
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
        TokenData, Security(get_current_user, scopes=["ga:de", "ga:de:own"])
    ],
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Route to delete bed note.

    :param note_id: UUID
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: dict
    """

    note = await BedNoteCRUD.get_note(session=session, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    bed = await BedCRUD.get_bed(session=session, bed_id=note.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:re"
    )

    if not await BedNoteCRUD.delete_note(session, note_id):
        raise HTTPException(status_code=404, detail="Note not found")

    log_handler.log_garden_event(
        event="Delete BedNote",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": bed.garden_id,
            "bed_id": bed.id,
            "note_id": note.id,
            "action": "delete_bed_note",
            "resource": "bed_note_routes",
        },
    )

    return {"message": "Note deleted successfully"}
