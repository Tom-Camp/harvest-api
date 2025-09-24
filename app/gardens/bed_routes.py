from typing import List
from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.gardens.bed_crud import BedCRUD
from app.gardens.bed_models import Bed
from app.gardens.bed_schemas import BedCreate, BedList, BedRead, BedUpdate
from app.logging import get_logger, log_handler
from app.users.user_models import User
from app.utils.database import get_db

logger = get_logger(__name__)

bed_router = APIRouter(prefix="/beds")


@bed_router.post("", response_model=Bed)
async def create_bed(
    bed: BedCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Bed:

    subject: str = casbin_subject(current_user.id)
    allowed = enforcer.enforce(subject, "garden", "create")
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    new_bed = await BedCRUD.create_bed(
        bed=bed,
        session=session,
    )
    logger.info(
        event="Bed create",
        severity="moderate",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": new_bed.garden_id,
            "bed_id": new_bed.id,
            "bed_name": new_bed.name,
            "action": "create_bed",
            "resource": "bed_routes",
        },
    )

    return new_bed


@bed_router.get("/{garden_id/", response_model=List[BedList])
async def read_beds(
    garden_id: UUID,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
):
    return await BedCRUD.get_beds(
        garden_id=garden_id,
        session=session,
        skip=skip,
        limit=limit,
    )


@bed_router.get("/{bed_id}", response_model=BedRead)
async def read_bed(
    bed_id: UUID,
    session: AsyncSession = Depends(get_db),
):

    bed = await BedCRUD.get_bed(session=session, bed_id=bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    return bed


@bed_router.put("/{bed_id}", response_model=Bed)
async def update_bed(
    bed_id: UUID,
    bed_update: BedUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Bed | None:

    bed = await BedCRUD.get_bed(session=session, bed_id=bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    user_subject = casbin_subject(current_user.id)
    bed_resource = casbin_object("p", bed.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, bed_resource, "update")

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, bed):
        raise HTTPException(status_code=403, detail="Forbidden")

    updated_bed = await BedCRUD.update_bed(
        session=session,
        bed_id=bed_id,
        bed_update=bed_update,
    )
    if updated_bed:
        log_handler.log_security_event(
            event="Bed updated",
            severity="low",
            context={
                "actor_id": current_user.id,
                "event_type": "security",
                "actor_username": current_user.username,
                "garden_id": updated_bed.garden_id,
                "bed_id": updated_bed.id,
                "bed_name": updated_bed.name,
                "action": "updated_bed",
                "resource": "bed_routes",
            },
        )
    return updated_bed


@bed_router.delete("/{bed_id}")
async def delete_bed(
    bed_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:

    bed = await BedCRUD.get_bed(session=session, bed_id=bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    user_subject = casbin_subject(current_user.id)
    bed_resource = casbin_object("p", bed.garden_id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, bed_resource, "update")

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, bed):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not await BedCRUD.delete_bed(session, bed_id):
        raise HTTPException(status_code=404, detail="Bed not found")

    log_handler.log_security_event(
        event="Bed deleted",
        severity="moderate",
        context={
            "event_type": "security",
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": bed.garden_id,
            "bed_id": bed.id,
            "bed_name": bed.name,
            "action": "delete_bed",
            "resource": "bed_routes",
        },
    )

    return {"message": "Bed deleted successfully"}
