from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.auth import get_current_user
from app.core.utils.database import AsyncSessionLocal, get_db
from app.core.utils.garden_helpers import check_garden_access
from app.logging import get_logger, log_handler
from app.models.garden_models import Garden, GardenNote
from app.schemas.auth_schemas import TokenData
from app.schemas.garden_note_schemas import (
    GardenNoteCreate,
    GardenNoteList,
    GardenNoteUpdate,
)
from app.services.garden_note_service import GardenNoteService

logger = get_logger(__name__)

garden_note_router = APIRouter(prefix="/garden-notes")


def get_garden_note_service() -> GardenNoteService:
    return GardenNoteService(session=AsyncSessionLocal())


@garden_note_router.post("/", response_model=GardenNote)
async def create_garden_note(
    note: GardenNoteCreate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: GardenNoteService = Depends(get_garden_note_service),
    session: AsyncSession = Depends(get_db),
) -> GardenNote:
    """
    A Route to create a GardenNote

    :param note: The GardenNoteCreate object; gardens.garden_note_schema.GardenNoteCreate
    :param current_user: The current user
    :param service: GardenNoteService; services.garden_note_service.GardenNoteService
    :param session: The SQLAlchemy asyncio AsyncSession
    :return: GardenNote; gardens.garden_models.GardenNote
    """

    garden = await session.get(Garden, note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:up"
    )

    new_note = await service.create_note(note=note)
    log_handler.log_garden_event(
        event="Note create",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": new_note.garden_id,
            "note_id": new_note.id,
            "action": "create_garden_note",
            "resource": "garden_note_routes",
        },
    )

    return new_note


@garden_note_router.get("/{note_id}", response_model=GardenNote)
async def read_garden_note(
    note_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    service: GardenNoteService = Depends(get_garden_note_service),
    session: AsyncSession = Depends(get_db),
) -> GardenNote:
    """
    Route to get a GardenNote

    :param note_id: The note object ID
    :param current_user: The current user
    :param service: GardenNoteService; services.garden_note_service.GardenNoteService
    :param session: The SQLAlchemy asyncio AsyncSession
    :return: A GardenNote; gardens.garden_models.GardenNote
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await session.get(Garden, note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:re"
    )

    return note


@garden_note_router.get("/notes/{garden_id}", response_model=list[GardenNoteList])
async def read_garden_notes(
    garden_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    skip: int = 0,
    limit: int = 100,
    service: GardenNoteService = Depends(get_garden_note_service),
    session: AsyncSession = Depends(get_db),
) -> list[GardenNoteList]:
    """
    Route to get a list of GardenNotes

    :param garden_id: The ID of the Garden to retrieve notes
    :param skip: The rows to skip
    :param limit: The number of rows to return
    :param current_user: The current user
    :param service: GardenNoteService; services.garden_note_service.GardenNoteService
    :param session: The SQLAlchemy asyncio AsyncSession
    :return: A list of GardenNote objects; gardens.garden_models.GardenNote
    """

    garden = await session.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:re"
    )

    notes = await service.get_notes(garden_id=garden_id, skip=skip, limit=limit)
    return [GardenNoteList.model_validate(note) for note in notes]


@garden_note_router.put("/{note_id}", response_model=GardenNote)
async def update_garden_note(
    note_id: UUID,
    note_update: GardenNoteUpdate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: GardenNoteService = Depends(get_garden_note_service),
    session: AsyncSession = Depends(get_db),
) -> GardenNote | None:
    """
    Route to update a GardenNote

    :param note_id: The ID of the GardenNote to update
    :param note_update: The GardenNoteUpdate object; gardens.garden_note_schemas.GardenNoteUpdate
    :param current_user: The current user
    :param service: GardenNoteService; services.garden_note_service.GardenNoteService
    :param session: The SQLAlchemy asyncio AsyncSession
    :return: GardenNote; gardens.garden_models.GardenNote
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await session.get(Garden, note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:up"
    )

    updated_note = await service.update_note(note_id=note_id, note_update=note_update)
    if updated_note:
        log_handler.log_garden_event(
            event="Note updated",
            context={
                "actor_id": current_user.id,
                "actor_username": current_user.username,
                "garden_id": updated_note.garden_id,
                "note_id": updated_note.id,
                "action": "update_note",
                "resource": "garden_note_routes",
            },
        )
    return updated_note


@garden_note_router.delete("/{note_id}")
async def delete_note(
    note_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:de", "ga:de:own"])
    ],
    service: GardenNoteService = Depends(get_garden_note_service),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    A route to delete a GardenNote

    :param note_id: The ID of the GardenNote to delete
    :param current_user: The current user
    :param service: GardenNoteService; services.garden_note_service.GardenNoteService
    :param session: The SQLAlchemy asyncio AsyncSession
    :return: dict
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    garden = await session.get(Garden, note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:de"
    )

    log_handler.log_garden_event(
        event="Note deleted",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": note.garden_id,
            "note_id": note.id,
            "action": "delete_note",
            "resource": "garden_note_routes",
        },
    )

    return {"message": "Note deleted successfully"}
