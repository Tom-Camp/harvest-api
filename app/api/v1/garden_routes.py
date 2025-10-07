from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException

from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_subject
from app.core.auth import get_current_active_user
from app.core.helpers.garden_helpers import garden_check_access
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.models.garden_models import Garden
from app.models.user_models import User
from app.schemas.garden_schemas import (
    GardenCreate,
    GardenList,
    GardenRead,
    GardenUpdate,
)
from app.services.garden_service import GardenService

logger = get_logger(__name__)

garden_router = APIRouter(prefix="/gardens")


def get_garden_service() -> GardenService:
    return GardenService(session=AsyncSessionLocal())


@garden_router.post("/", response_model=Garden)
async def create_garden(
    garden: GardenCreate,
    service: GardenService = Depends(get_garden_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Garden:
    """
    A route to create a Garden object

    :param garden: The GardenCreate object; gardens.garden_schemas.GardenCreate
    :param service: GardenService; services.garden_service.GardenService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: Garden; garden.garden_models.Garden
    """

    subject: str = casbin_subject(current_user.id)
    allowed = enforcer.enforce(subject, "garden", "create")
    if not allowed:
        logger.debug(f"User: {current_user.username}: allowed {allowed}")
        raise HTTPException(status_code=403, detail="Forbidden")

    new_garden = await service.create_garden(garden=garden, user=current_user)
    log_handler.log_garden_event(
        event="Garden create",
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
    service: GardenService = Depends(get_garden_service),
) -> list[GardenList]:
    """
    A route to get all Garden objects

    :param skip: The number of Garden objects to skip
    :param limit: The number of Garden objects to return
    :param service: GardenService; services.garden_service.GardenService
    :return: The list of GardenList objects; gardens.garden_schemas.GardenList
    """

    gardens = await service.get_gardens(skip=skip, limit=limit)
    return [GardenList.model_validate(garden) for garden in gardens]


@garden_router.get("/user/{user_id}", response_model=list[GardenList])
async def read_user_gardens(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: GardenService = Depends(get_garden_service),
) -> list[GardenList]:
    """
    A route to get all Garden objects for a given user

    :param user_id: The user ID
    :param skip: The number of Garden objects to skip
    :param limit: The number of Garden objects to return
    :param service: GardenService; services.garden_service.GardenService
    :return: The list of GardenList objects; gardens.garden_schemas.GardenList
    """
    session = AsyncSessionLocal()
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    gardens = await service.get_user_gardens(user_id=user_id, skip=skip, limit=limit)
    return [GardenList.model_validate(garden) for garden in gardens]


@garden_router.get("/my", response_model=list[GardenList])
async def read_my_gardens(
    skip: int = 0,
    limit: int = 100,
    service: GardenService = Depends(get_garden_service),
    current_user: User = Depends(get_current_active_user),
) -> list[GardenList]:
    """
    A route to get all Garden objects for a given user

    :param skip: The number of Garden objects to skip
    :param limit: The number of Garden objects to return
    :param service: GardenService; services.garden_service.GardenService
    :param current_user: The User accessing the route
    :return: The list of GardenList objects; gardens.garden_schemas.GardenList
    """

    gardens = await service.get_user_gardens(
        user_id=current_user.id, skip=skip, limit=limit
    )
    return [GardenList.model_validate(garden) for garden in gardens]


@garden_router.get("/{garden_id}", response_model=GardenRead)
async def read_garden(
    garden_id: UUID,
    service: GardenService = Depends(get_garden_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Garden:
    """
    A route to get a Garden object by ID

    :param garden_id: The ID of the Garden object
    :param service: GardenService; services.garden_service.GardenService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: The GardenRead object; gardens.garden_schemas.GardenRead
    """

    _ = await garden_check_access(
        garden_id=garden_id,
        enforcer=enforcer,
        current_user=current_user,
        action="read",
    )

    garden = await service.get_garden(garden_id=garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    return garden


@garden_router.put("/{garden_id}", response_model=Garden)
async def update_garden(
    garden_id: UUID,
    garden_update: GardenUpdate,
    service: GardenService = Depends(get_garden_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Garden | None:
    """
    A route to update a Garden object

    :param garden_id: The ID of the Garden object
    :param garden_update: The GardenUpdate object; gardens.garden_schemas.GardenUpdate
    :param service: GardenService; services.garden_service.GardenService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: The updated Garden object; gardens.garden_models.Garden
    """

    _ = await garden_check_access(
        garden_id=garden_id,
        enforcer=enforcer,
        current_user=current_user,
        action="update",
    )

    updated_garden = await service.update_garden(
        garden_id=garden_id, garden_update=garden_update
    )
    if updated_garden:
        log_handler.log_garden_event(
            event="Garden updated",
            context={
                "actor_id": current_user.id,
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
    service: GardenService = Depends(get_garden_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:
    """
    A route to delete a Garden object

    :param garden_id: The ID of the Garden object
    :param service: GardenService; services.garden_service.GardenService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: dict
    """

    garden = await garden_check_access(
        garden_id=garden_id,
        enforcer=enforcer,
        current_user=current_user,
        action="delete",
    )

    if not await service.delete_garden(garden_id=garden_id):
        raise HTTPException(status_code=404, detail="Garden not found")

    log_handler.log_garden_event(
        event="Delete Garden",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": garden.id,
            "garden_name": garden.name,
            "action": "delete_garden",
            "resource": "garden_routes",
        },
    )

    return {"message": "Garden deleted successfully"}
