from typing import Sequence
from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.beds.bed_crud import BedCRUD
from app.beds.bed_models import BedNote
from app.beds.bed_note_crud import BedNoteCRUD
from app.beds.bed_note_schemas import BedNoteCreate, BedNoteList, BedNoteUpdate
from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.gardens.garden_crud import GardenCRUD
from app.logging import get_logger, log_handler
from app.users.user_models import User
from app.utils.database import get_db

logger = get_logger(__name__)

bed_note_router = APIRouter(prefix="/bed-notes")


@bed_note_router.post("/", response_model=BedNote)
async def create_bed_note(
    note: BedNoteCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> BedNote:

    bed = await BedCRUD.get_bed(session=session, bed_id=note.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await GardenCRUD.get_garden(session, bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "create")

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    new_note = await BedNoteCRUD.create_note(
        note=note,
        session=session,
    )
    log_handler.log_garden_event(
        event="Note create",
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


@bed_note_router.get("/{note_id}", response_model=BedNote)
async def get_bed_note(
    note_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> BedNote:

    note = await BedNoteCRUD.get_note(note_id=note_id, session=session)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    bed = await BedCRUD.get_bed(session=session, bed_id=note.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await GardenCRUD.get_garden(session, bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "read")

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    return note


@bed_note_router.get("/notes/{bed_id}", response_model=Sequence[BedNoteList])
async def read_notes(
    bed_id: UUID,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
):

    bed = await BedCRUD.get_bed(session=session, bed_id=bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "read")

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    return await BedNoteCRUD.get_notes(
        bed_id=bed_id,
        session=session,
        skip=skip,
        limit=limit,
    )


@bed_note_router.put("/{note_id}", response_model=BedNote)
async def update_garden_note(
    note_id: UUID,
    note_update: BedNoteUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> BedNote:

    note = await BedNoteCRUD.get_note(note_id=note_id, session=session)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    bed = await BedCRUD.get_bed(session=session, bed_id=note.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "update")

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    updated_note = await BedNoteCRUD.update_note(
        session=session,
        note_id=note_id,
        note_update=note_update,
    )
    if updated_note:
        log_handler.log_garden_event(
            event="Garden Note updated",
            context={
                "actor_id": current_user.id,
                "actor_username": current_user.username,
                "garden_id": garden.id,
                "bed_id": updated_note.bed_id,
                "note_id": updated_note.id,
                "action": "update_note",
                "resource": "bed_note_routes",
            },
        )
    return updated_note
