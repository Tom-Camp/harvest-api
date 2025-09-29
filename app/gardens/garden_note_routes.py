from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.gardens.garden_crud import GardenCRUD
from app.gardens.garden_models import GardenNote
from app.gardens.garden_note_crud import GardenNoteCRUD
from app.gardens.garden_note_schemas import (
    GardenNoteCreate,
    GardenNoteList,
    GardenNoteUpdate,
)
from app.logging import get_logger, log_handler
from app.users.user_models import User
from app.utils.database import get_db

logger = get_logger(__name__)

garden_note_router = APIRouter(prefix="/garden-notes")


@garden_note_router.post("/", response_model=GardenNote)
async def create_garden_note(
    note: GardenNoteCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> GardenNote:

    garden = await GardenCRUD.get_garden(session, note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "create")

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    new_note = await GardenNoteCRUD.create_note(
        note=note,
        session=session,
    )
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
async def get_garden_note(
    note_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> GardenNote:

    note = await GardenNoteCRUD.get_note(note_id=note_id, session=session)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await GardenCRUD.get_garden(session, note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "read")

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    return note


@garden_note_router.get("/notes/{garden_id}", response_model=list[GardenNoteList])
async def read_garden_notes(
    garden_id: UUID,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> list[GardenNoteList]:

    garden = await GardenCRUD.get_garden(session=session, garden_id=garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "read")

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    notes = await GardenNoteCRUD.get_notes(
        garden_id=garden_id,
        session=session,
        skip=skip,
        limit=limit,
    )
    return [GardenNoteList.model_validate(note) for note in notes]


@garden_note_router.put("/{note_id}", response_model=GardenNote)
async def update_garden_note(
    note_id: UUID,
    note_update: GardenNoteUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> GardenNote:

    note = await GardenNoteCRUD.get_note(note_id=note_id, session=session)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "update")

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    updated_note = await GardenNoteCRUD.update_note(
        session=session,
        note_id=note_id,
        note_update=note_update,
    )
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
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:

    note = await GardenNoteCRUD.get_note(session=session, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    user_subject = casbin_subject(current_user.id)
    note_resource = casbin_object("ga", note.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, note_resource, "delete")

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not await GardenNoteCRUD.delete_note(session, note_id):
        raise HTTPException(status_code=404, detail="Note not found")

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
