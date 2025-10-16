from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.auth import get_current_user
from app.core.utils.database import AsyncSessionLocal, get_db
from app.core.utils.garden_helpers import check_garden_access
from app.logging import get_logger, log_handler
from app.models.garden_models import Garden
from app.models.user_models import User
from app.schemas.auth_schemas import TokenData
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
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["ga:cr"])],
    service: GardenService = Depends(get_garden_service),
) -> Garden:
    """
    A route to create a Garden object

    :param garden: The GardenCreate object; gardens.garden_schemas.GardenCreate
    :param service: GardenService; services.garden_service.GardenService
    :param current_user: The current user
    :return: Garden; garden.garden_models.Garden
    """

    new_garden = await service.create_garden(garden=garden, user_id=current_user.id)
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
    session: AsyncSession = Depends(get_db),
) -> list[GardenList]:
    """
    A route to get all Garden objects for a given user

    :param user_id: The user ID
    :param skip: The number of Garden objects to skip
    :param limit: The number of Garden objects to return
    :param service: GardenService; services.garden_service.GardenService
    :param session: SQLAlchemy AsyncSession
    :return: The list of GardenList objects; gardens.garden_schemas.GardenList
    """
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    gardens = await service.get_user_gardens(user_id=user_id, skip=skip, limit=limit)
    return [GardenList.model_validate(garden) for garden in gardens]


@garden_router.get("/my", response_model=list[GardenList])
async def read_my_gardens(
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    skip: int = 0,
    limit: int = 100,
    service: GardenService = Depends(get_garden_service),
) -> list[GardenList]:
    """
    A route to get all Garden objects for a given user

    :param skip: The number of Garden objects to skip
    :param limit: The number of Garden objects to return
    :param service: GardenService; services.garden_service.GardenService
    :param current_user: The User accessing the route
    :return: The list of GardenList objects; gardens.garden_schemas.GardenList
    """

    gardens = await service.get_user_gardens(current_user.id, skip=skip, limit=limit)

    return [GardenList.model_validate(garden) for garden in gardens]


@garden_router.get("/{garden_id}", response_model=GardenRead)
async def read_garden(
    garden_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    service: GardenService = Depends(get_garden_service),
) -> Garden:
    """
    A route to get a Garden object by ID

    :param garden_id: The ID of the Garden object
    :param current_user: The current user
    :param service: GardenService; services.garden_service.GardenService
    :return: The GardenRead object; gardens.garden_schemas.GardenRead
    """

    garden = await service.get_garden(garden_id=garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:re"
    )

    return garden


@garden_router.put("/{garden_id}", response_model=Garden)
async def update_garden(
    garden_id: UUID,
    garden_update: GardenUpdate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: GardenService = Depends(get_garden_service),
) -> Garden | None:
    """
    A route to update a Garden object

    :param garden_id: The ID of the Garden object
    :param garden_update: The GardenUpdate object; gardens.garden_schemas.GardenUpdate
    :param current_user: The current user
    :param service: GardenService; services.garden_service.GardenService
    :return: The updated Garden object; gardens.garden_models.Garden
    """

    garden = await service.get_garden(garden_id=garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:up"
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
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:de", "ga:de:own"])
    ],
    service: GardenService = Depends(get_garden_service),
) -> dict:
    """
    A route to delete a Garden object

    :param garden_id: The ID of the Garden object
    :param current_user: The current user
    :param service: GardenService; services.garden_service.GardenService
    :return: dict
    """

    garden = await service.get_garden(garden_id=garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:de"
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
