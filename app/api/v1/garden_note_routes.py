from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException

from app.casbin.casbin_config import get_casbin_enforcer
from app.core.auth import get_current_active_user
from app.core.helpers.garden_helpers import garden_note_check_access
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.models.garden_models import GardenNote
from app.models.user_models import User
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
    service: GardenNoteService = Depends(get_garden_note_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> GardenNote:
    """
    A Route to create a GardenNote

    :param note: The GardenNoteCreate object; gardens.garden_note_schema.GardenNoteCreate
    :param service: GardenNoteService; services.garden_note_services.GardenNoteService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: GardenNote; gardens.garden_models.GardenNote
    """

    await garden_note_check_access(
        garden_id=note.garden_id,
        enforcer=enforcer,
        current_user=current_user,
        action="create",
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
    service: GardenNoteService = Depends(get_garden_note_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> GardenNote:
    """
    Route to get a GardenNote

    :param note_id: The note object ID
    :param service: GardenNoteService; services.garden_note_services.GardenNoteService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: A GardenNote; gardens.garden_models.GardenNote
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    await garden_note_check_access(
        garden_id=note.garden_id,
        enforcer=enforcer,
        current_user=current_user,
        action="read",
    )

    return note


@garden_note_router.get("/notes/{garden_id}", response_model=list[GardenNoteList])
async def read_garden_notes(
    garden_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: GardenNoteService = Depends(get_garden_note_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> list[GardenNoteList]:
    """
    Route to get a list of GardenNotes

    :param garden_id: The ID of the Garden to retrieve notes
    :param skip: The rows to skip
    :param limit: The number of rows to return
    :param service: GardenNoteService; services.garden_note_services.GardenNoteService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: A list of GardenNote objects; gardens.garden_models.GardenNote
    """

    await garden_note_check_access(
        garden_id=garden_id,
        enforcer=enforcer,
        current_user=current_user,
        action="read",
    )

    notes = await service.get_notes(garden_id=garden_id, skip=skip, limit=limit)
    return [GardenNoteList.model_validate(note) for note in notes]


@garden_note_router.put("/{note_id}", response_model=GardenNote)
async def update_garden_note(
    note_id: UUID,
    note_update: GardenNoteUpdate,
    service: GardenNoteService = Depends(get_garden_note_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> GardenNote:
    """
    Route to update a GardenNote

    :param note_id: The ID of the GardenNote to update
    :param note_update: The GardenNoteUpdate object; gardens.garden_note_schemas.GardenNoteUpdate
    :param service: GardenNoteService; services.garden_note_services.GardenNoteService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: GardenNote; gardens.garden_models.GardenNote
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    await garden_note_check_access(
        garden_id=note.garden_id,
        enforcer=enforcer,
        current_user=current_user,
        action="read",
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
    service: GardenNoteService = Depends(get_garden_note_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:
    """
    A route to delete a GardenNote

    :param note_id: The ID of the GardenNote to delete
    :param service: GardenNoteService; services.garden_note_services.GardenNoteService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: dict
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    await garden_note_check_access(
        garden_id=note.garden_id,
        enforcer=enforcer,
        current_user=current_user,
        action="read",
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
