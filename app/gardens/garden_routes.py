from typing import Sequence
from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.gardens.garden_crud import GardenCRUD
from app.gardens.garden_models import Garden
from app.gardens.garden_schemas import (
    GardenCreate,
    GardenList,
    GardenRead,
    GardenUpdate,
)
from app.logging import get_logger, log_handler
from app.users.user_models import User
from app.utils.database import get_db

logger = get_logger(__name__)

garden_router = APIRouter(prefix="/gardens")


@garden_router.post("/", response_model=Garden)
async def create_garden(
    garden: GardenCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Garden:

    subject: str = casbin_subject(current_user.id)
    allowed = enforcer.enforce(subject, "garden", "create")
    if not allowed:
        logger.debug(f"User: {current_user.username}: allowed {allowed}")
        raise HTTPException(status_code=403, detail="Forbidden")

    new_garden = await GardenCRUD.create_garden(
        garden=garden, session=session, user=current_user
    )
    logger.info(
        event="Garden create",
        severity="moderate",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": new_garden.id,
            "garden_name": new_garden.name,
            "action": "create_garden",
            "resource": "garden_routes",
        },
    )

    return new_garden


@garden_router.get("/", response_model=list[GardenList])
async def read_gardens(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
):

    return await GardenCRUD.get_gardens(session, skip=skip, limit=limit)


@garden_router.get("/user/{user_id}", response_model=list[GardenList])
async def read_user_gardens(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
):

    return await GardenCRUD.get_user_gardens(
        session=session, user_id=user_id, skip=skip, limit=limit
    )


@garden_router.get("/my", response_model=list[GardenList])
async def read_my_gardens(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Sequence:

    return await GardenCRUD.get_user_gardens(
        session, current_user.id, skip=skip, limit=limit
    )


@garden_router.get("/{garden_id}", response_model=GardenRead)
async def read_garden(
    garden_id: UUID,
    session: AsyncSession = Depends(get_db),
):

    garden = await GardenCRUD.get_garden(session=session, garden_id=garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    return garden


@garden_router.put("/{garden_id}", response_model=Garden)
async def update_garden(
    garden_id: UUID,
    garden_update: GardenUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Garden | None:

    garden = await GardenCRUD.get_garden(session, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    user_subject = casbin_subject(current_user.id)
    garden_resource = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "update")

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    updated_garden = await GardenCRUD.update_garden(
        session=session,
        garden_id=garden_id,
        garden_update=garden_update,
    )
    if updated_garden:
        log_handler.log_security_event(
            event="Garden updated",
            severity="low",
            context={
                "actor_id": current_user.id,
                "event_type": "security",
                "actor_username": current_user.username,
                "garden_id": updated_garden.id,
                "garden_name": updated_garden.name,
                "action": "update_garden",
                "resource": "garden_routes",
            },
        )
    return updated_garden


@garden_router.delete("/{garden_id}")
async def delete_garden(
    garden_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:

    garden = await GardenCRUD.get_garden(session=session, garden_id=garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    user_subject = casbin_subject(current_user.id)
    garden_resource = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "delete")

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not await GardenCRUD.delete_garden(session, garden_id):
        raise HTTPException(status_code=404, detail="Garden not found")

    log_handler.log_security_event(
        event="Garden deleted",
        severity="moderate",
        context={
            "event_type": "security",
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": garden.id,
            "garden_name": garden.name,
            "action": "delete_garden",
            "resource": "garden_routes",
        },
    )

    return {"message": "Garden deleted successfully"}
