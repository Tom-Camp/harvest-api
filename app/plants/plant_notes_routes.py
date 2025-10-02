from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.beds.bed_crud import BedCRUD
from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.gardens.garden_crud import GardenCRUD
from app.logging import get_logger, log_handler
from app.plants.plant_crud import PlantCRUD
from app.plants.plant_models import PlantNote
from app.plants.plant_notes_crud import PlantNoteCRUD
from app.plants.plant_notes_schemas import PlantNoteCreate, PlantNoteRead
from app.users.user_models import User
from app.utils.database import get_db

logger = get_logger(__name__)

plant_note_router = APIRouter(prefix="/plant-notes")


@plant_note_router.post("/", response_model=PlantNote)
async def create_plant_note(
    note: PlantNoteCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> PlantNote:
    """
    Route for creating a plant note.

    :param note: PlantNoteCreate; plants.plant_note_schemas.PlantNoteCreate
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: PlantNote
    """

    plant = await PlantCRUD.get_plant(session=session, plant_id=note.plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Not found")

    bed = await BedCRUD.get_bed(session=session, bed_id=plant.bed_id)
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

    new_note = await PlantNoteCRUD.create_note(
        note=note,
        session=session,
    )
    log_handler.log_garden_event(
        event="Note create",
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
async def get_bed_note(
    note_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> PlantNoteRead:
    """
    Route for getting a plant note.

    :param note_id: UUID
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: BedNoteRead; beds.bed_note_schemas.BedNoteRead
    """

    note = await PlantNoteCRUD.get_note(note_id=note_id, session=session)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    plant = await PlantCRUD.get_plant(session=session, plant_id=note.plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Not found")

    bed = await BedCRUD.get_bed(session=session, bed_id=plant.bed_id)
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
