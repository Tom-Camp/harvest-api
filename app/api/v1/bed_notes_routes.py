from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException

from app.casbin.casbin_config import get_casbin_enforcer
from app.core.auth import get_current_active_user
from app.core.helpers.bed_helpers import bed_note_check_access
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.models.bed_models import BedNote
from app.models.user_models import User
from app.schemas.bed_notes_schemas import (
    BedNoteCreate,
    BedNoteList,
    BedNoteRead,
    BedNoteUpdate,
)
from app.services.bed_notes_service import BedNoteService

logger = get_logger(__name__)

bed_note_router = APIRouter(prefix="/bed-notes")


def get_bed_service() -> BedNoteService:
    return BedNoteService(session=AsyncSessionLocal())


@bed_note_router.post("/", response_model=BedNote)
async def create_bed_note(
    note: BedNoteCreate,
    service: BedNoteService = Depends(get_bed_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> BedNote:
    """
    Route for creating a bed note.

    :param note: BedNoteCreate; beds.bed_note_schemas.BedNoteCreate
    :param service: BedNoteService; serivices.bed_note_service.BedNoteService
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: BedNote
    """

    bed, garden = await bed_note_check_access(
        bed_id=note.bed_id,
        current_user=current_user,
        enforcer=enforcer,
        action="create",
    )

    new_note = await service.create_note(note=note)
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
    service: BedNoteService = Depends(get_bed_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> BedNote:
    """
    Route for getting a bed note.

    :param note_id: UUID
    :param service: BedNoteService; serivices.bed_note_service.BedNoteService
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: BedNoteRead; beds.bed_note_schemas.BedNoteRead
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    _, _ = await bed_note_check_access(
        bed_id=note.bed_id,
        current_user=current_user,
        enforcer=enforcer,
        action="create",
    )

    return note


@bed_note_router.get("/notes/{bed_id}", response_model=list[BedNoteList])
async def read_bed_notes(
    bed_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: BedNoteService = Depends(get_bed_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> list[BedNoteList]:
    """
    Route for getting a list of bed notes.

    :param bed_id: UUID
    :param skip: number of rows to skip
    :param limit: limit number of rows to return
    :param service: BedNoteService; serivices.bed_note_service.BedNoteService
    :param current_user: User
    """

    _, _ = await bed_note_check_access(
        bed_id=bed_id,
        current_user=current_user,
        enforcer=enforcer,
        action="create",
    )

    notes = await service.get_notes(bed_id=bed_id, skip=skip, limit=limit)
    return [BedNoteList.model_validate(note) for note in notes]


@bed_note_router.put("/{note_id}", response_model=BedNote)
async def update_bed_note(
    note_id: UUID,
    note_update: BedNoteUpdate,
    service: BedNoteService = Depends(get_bed_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> BedNote | None:
    """
    Route for updating a bed note.

    :param note_id: UUID
    :param note_update: BedNoteUpdate object; beds.bed_note_schemas.BedNoteUpdate
    :param service: BedNoteService; serivices.bed_note_service.BedNoteService
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: BedNote
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    _, garden = await bed_note_check_access(
        bed_id=note.bed_id,
        current_user=current_user,
        enforcer=enforcer,
        action="create",
    )

    updated_note = await service.update_note(note_id=note_id, note_update=note_update)
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
    service: BedNoteService = Depends(get_bed_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:
    """
    Route to delete bed note.

    :param note_id: UUID
    :param service: BedNoteService; serivices.bed_note_service.BedNoteService
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: dict
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    bed, _ = await bed_note_check_access(
        bed_id=note.bed_id,
        current_user=current_user,
        enforcer=enforcer,
        action="create",
    )

    if not await service.delete_note(note_id=note_id):
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
