from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException

from app.casbin.casbin_config import get_casbin_enforcer
from app.core.auth import get_current_active_user
from app.core.helpers.plant_helpers import plant_note_check_access
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.models.plant_models import PlantNote
from app.models.user_models import User
from app.schemas.plant_notes_schemas import (
    PlantNoteCreate,
    PlantNoteList,
    PlantNoteRead,
    PlantNoteUpdate,
)
from app.services.plant_notes_service import PlantNoteService

logger = get_logger(__name__)

plant_note_router = APIRouter(prefix="/plant-notes")


def get_plant_service() -> PlantNoteService:
    return PlantNoteService(session=AsyncSessionLocal())


@plant_note_router.post("/", response_model=PlantNote)
async def create_plant_note(
    note: PlantNoteCreate,
    service: PlantNoteService = Depends(get_plant_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> PlantNote:
    """
    Route for creating a plant note.

    :param note: PlantNoteCreate; plants.plant_note_schemas.PlantNoteCreate
    :param service: PlantNoteService; serivices.plant_note_service.PlantNoteService
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: PlantNote
    """

    bed, garden = await plant_note_check_access(
        plant_id=note.plant_id,
        user=current_user,
        enforcer=enforcer,
        action="create",
    )

    new_note = await service.create_note(note=note)
    log_handler.log_garden_event(
        event="Create PlantNote",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": garden.id,
            "bed": bed.id,
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
    service: PlantNoteService = Depends(get_plant_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> PlantNote:
    """
    Route for getting a plant note.

    :param note_id: UUID
    :param service: PlantNoteService; serivices.plant_note_service.PlantNoteService
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: PlantNoteRead; plants.plant_note_schemas.PlantNoteRead
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    _, _ = await plant_note_check_access(
        plant_id=note.plant_id,
        user=current_user,
        enforcer=enforcer,
        action="read",
    )

    return note


@plant_note_router.get("/notes/{plant_id}", response_model=list[PlantNoteList])
async def read_plant_notes(
    plant_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: PlantNoteService = Depends(get_plant_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> list[PlantNoteList]:
    """
    Route for getting a list of plant notes.

    :param plant_id: UUID
    :param skip: number of rows to skip
    :param limit: limit number of rows to return
    :param service: PlantNoteService; serivices.plant_note_service.PlantNoteService
    :param current_user: User
    """

    _, _ = await plant_note_check_access(
        plant_id=plant_id,
        user=current_user,
        enforcer=enforcer,
        action="read",
    )

    notes = await service.get_notes(plant_id=plant_id, skip=skip, limit=limit)
    return [PlantNoteList.model_validate(note) for note in notes]


@plant_note_router.put("/{note_id}", response_model=PlantNote)
async def update_plant_note(
    note_id: UUID,
    note_update: PlantNoteUpdate,
    service: PlantNoteService = Depends(get_plant_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> PlantNote | None:
    """
    Route for updating a bed note.

    :param note_id: UUID
    :param note_update: PlantNoteUpdate object; plants.plant_note_schemas.PlantNoteUpdate
    :param service: PlantNoteService; serivices.plant_note_service.PlantNoteService
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: PlantNote
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    bed, garden = await plant_note_check_access(
        plant_id=note.plant_id,
        user=current_user,
        enforcer=enforcer,
        action="create",
    )

    updated_note = await service.update_note(note_id=note_id, note_update=note_update)
    if updated_note:
        log_handler.log_garden_event(
            event="Update PlantNote",
            context={
                "actor_id": current_user.id,
                "actor_username": current_user.username,
                "garden_id": garden.id,
                "bed_id": bed.id,
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
    service: PlantNoteService = Depends(get_plant_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:
    """
    Route to delete bed note.

    :param note_id: UUID
    :param service: PlantNoteService; serivices.plant_note_service.PlantNoteService
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: dict
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    bed, garden = await plant_note_check_access(
        plant_id=note.plant_id,
        user=current_user,
        enforcer=enforcer,
        action="create",
    )

    if not await service.delete_note(note_id=note_id):
        raise HTTPException(status_code=404, detail="Note not found")

    log_handler.log_garden_event(
        event="Delete PlantNote",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": garden.id,
            "bed_id": bed.id,
            "plant_id": note.plant_id,
            "note_id": note.id,
            "action": "delete_plant_note",
            "resource": "plant_note_routes",
        },
    )

    return {"message": "Note deleted successfully"}
