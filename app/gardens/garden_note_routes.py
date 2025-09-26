from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.gardens.garden_crud import GardenCRUD
from app.gardens.garden_models import GardenNote
from app.gardens.garden_note_crud import GardenNoteCRUD
from app.gardens.garden_note_schemas import GardenNoteCreate
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
    log_handler.log_security_event(
        event="Note create",
        severity="low",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": new_note.garden_id,
            "bed_id": new_note.id,
            "action": "create_garden_note",
            "resource": "garden_note_routes",
        },
    )

    return new_note
