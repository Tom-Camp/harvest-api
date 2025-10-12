from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.logging import get_logger, log_handler
from app.plants.plant_models import PlantNote
from app.plants.plant_notes_crud import PlantNoteCRUD
from app.plants.plant_notes_schemas import (
    PlantNoteCreate,
    PlantNoteList,
    PlantNoteRead,
    PlantNoteUpdate,
)
from app.users.user_models import User
from app.utils.database import get_db

logger = get_logger(__name__)

plant_note_router = APIRouter(prefix="/plant-notes")


@plant_note_router.post("/", response_model=PlantNote)
async def create_plant_note(
    note: PlantNoteCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PlantNote:
    """
    Route for creating a plant note.

    :param note: PlantNoteCreate; plants.plant_note_schemas.PlantNoteCreate
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: PlantNote
    """

    new_note = await PlantNoteCRUD.create_note(
        note=note,
        session=session,
    )
    log_handler.log_garden_event(
        event="Create PlantNote",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            # "garden_id": garden.id,
            # "bed": bed.id,
            "plant_id": new_note.plant_id,
            "note_id": new_note.id,
            "action": "create_plant_note",
            "resource": "plant_note_routes",
        },
    )

    return new_note


@plant_note_router.get("/{note_id}", response_model=PlantNoteRead)
async def read_plant_note(
    note_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PlantNote:
    """
    Route for getting a plant note.

    :param note_id: UUID
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: PlantNoteRead; plants.plant_note_schemas.PlantNoteRead
    """

    note = await PlantNoteCRUD.get_note(note_id=note_id, session=session)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    return note


@plant_note_router.get("/notes/{plant_id}", response_model=list[PlantNoteList])
async def read_plant_notes(
    plant_id: UUID,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PlantNoteList]:
    """
    Route for getting a list of plant notes.

    :param plant_id: UUID
    :param skip: number of rows to skip
    :param limit: limit number of rows to return
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    """

    notes = await PlantNoteCRUD.get_notes(
        plant_id=plant_id,
        session=session,
        skip=skip,
        limit=limit,
    )
    return [PlantNoteList.model_validate(note) for note in notes]


@plant_note_router.put("/{note_id}", response_model=PlantNote)
async def update_plant_note(
    note_id: UUID,
    note_update: PlantNoteUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PlantNote:
    """
    Route for updating a bed note.

    :param note_id: UUID
    :param note_update: PlantNoteUpdate object; plants.plant_note_schemas.PlantNoteUpdate
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: PlantNote
    """

    note = await PlantNoteCRUD.get_note(note_id=note_id, session=session)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    updated_note = await PlantNoteCRUD.update_note(
        session=session,
        note_id=note_id,
        note_update=note_update,
    )
    if updated_note:
        log_handler.log_garden_event(
            event="Update PlantNote",
            context={
                "actor_id": current_user.id,
                "actor_username": current_user.username,
                # "garden_id": garden.id,
                # "bed_id": bed.id,
                "plant_id": updated_note.plant_id,
                "note_id": updated_note.id,
                "action": "update_plant_note",
                "resource": "plant_note_routes",
            },
        )
    return updated_note


@plant_note_router.delete("/{plant_id}")
async def delete_plant_note(
    note_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Route to delete bed note.

    :param note_id: UUID
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: dict
    """

    note = await PlantNoteCRUD.get_note(session=session, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if not await PlantNoteCRUD.delete_note(session, note_id):
        raise HTTPException(status_code=404, detail="Note not found")

    log_handler.log_garden_event(
        event="Delete PlantNote",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            # "garden_id": garden.id,
            # "bed_id": bed.id,
            "plant_id": note.plant_id,
            "note_id": note.id,
            "action": "delete_plant_note",
            "resource": "plant_note_routes",
        },
    )

    return {"message": "Note deleted successfully"}
