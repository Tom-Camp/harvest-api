from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.plant_info_agent import get_plant_info
from app.casbin.casbin_config import get_casbin_enforcer
from app.core.auth import get_current_active_user
from app.core.helpers.plant_helpers import map_ai_response_to_plant, plant_check_access
from app.core.utils.database import AsyncSessionLocal, get_db
from app.logging import get_logger, log_handler
from app.models.plant_models import Plant
from app.models.user_models import User
from app.schemas.plant_schemas import PlantCreate, PlantRead, PlantUpdate
from app.services.plant_service import PlantService

logger = get_logger(__name__)

plant_router = APIRouter(prefix="/plants")


def get_plant_service() -> PlantService:
    return PlantService(session=AsyncSessionLocal())


@plant_router.post("/", response_model=Plant)
async def create_plant(
    plant: PlantCreate,
    service: PlantService = Depends(get_plant_service),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Plant:
    """
    Create a Plant object

    :param plant: a PlantCreate object; plants.plant_schema.PlantCreate
    :param service: PlantService; services.plant_service.PlantService
    :param session: AsyncSession; SQLAlchemy asyncio AsyncSession
    :param current_user: User object for the user accessing the route.
    :param enforcer: Casbin AsyncEnforcer
    :return: Plant object; plants.plant_models.Plant
    """

    bed, garden = await plant_check_access(
        bed_id=plant.bed_id,
        user=current_user,
        enforcer=enforcer,
        action="create",
    )

    new_plant = await service.create_plant(plant=plant)
    location: str = garden.location
    check_plant: str = (
        f"{new_plant.variety} {new_plant.species}"
        if new_plant.variety
        else new_plant.species
    )
    plant_info = await get_plant_info(plant=check_plant, location=location)
    plant_info_mapped = await map_ai_response_to_plant(
        plant_id=new_plant.id, ai_recommendations=plant_info
    )

    session.add(plant_info_mapped)
    await session.commit()
    await session.refresh(new_plant)

    log_handler.log_garden_event(
        event="Plant create",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": bed.garden_id,
            "bed_id": bed.id,
            "plant_name": new_plant.species,
            "plant_id": new_plant.id,
            "action": "create_plant",
            "resource": "plant_routes",
        },
    )

    return new_plant


@plant_router.get("/{plant_id}", response_model=PlantRead)
async def read_plant(
    plant_id: UUID,
    service: PlantService = Depends(get_plant_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Plant:
    """
    Return a PlantRead object by the Plant ID

    :param plant_id: Unique ID for the plant
    :param service: PlantService; services.plant_service.PlantService
    :param current_user: User object for the user accessing the route.
    :param enforcer: Casbin AsyncEnforcer
    :return: PlantRead object; plants.plant_schemas.PlantRead
    """

    plant = await service.get_plant(plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    _, _ = await plant_check_access(
        bed_id=plant.bed_id,
        user=current_user,
        enforcer=enforcer,
        action="read",
    )

    return plant


@plant_router.put("/{plant_id}", response_model=PlantRead)
async def update_plant(
    plant_id: UUID,
    plant_update: PlantUpdate,
    service: PlantService = Depends(get_plant_service),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Plant | None:
    """
    A route for updating a Plant object

    :param plant_id: the Plant unique ID
    :param plant_update: a PlantUpdate object; plants.plant_schemas.PlantUpdate
    :param service: PlantService; services.plant_service.PlantService
    :param session: AsyncSession; SQLAlchemy asyncio AsyncSession
    :param current_user: the User making the request
    :param enforcer: Casbin AsyncEnforcer
    :return: PlantRead object; plants.plant_schemas.PlantRead
    """

    plant = await service.get_plant(plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    bed, garden = await plant_check_access(
        bed_id=plant.bed_id,
        user=current_user,
        enforcer=enforcer,
        action="updated",
    )

    updated_plant = await service.update_plant(
        plant_id=plant_id, plant_update=plant_update
    )
    if (
        updated_plant
        and hasattr(updated_plant, "variety")
        and updated_plant.variety != plant.variety
    ):
        location: str = garden.location
        check_plant: str = (
            f"{updated_plant.variety} {updated_plant.species}"
            if updated_plant.variety
            else updated_plant.species
        )
        plant_info = await get_plant_info(plant=check_plant, location=location)
        plant_info_mapped = await map_ai_response_to_plant(
            plant_id=updated_plant.id, ai_recommendations=plant_info
        )

        session.add(plant_info_mapped)
        await session.commit()
        await session.refresh(updated_plant)

    if updated_plant:
        log_handler.log_garden_event(
            event="Plant updated",
            context={
                "actor_id": current_user.id,
                "actor_username": current_user.username,
                "garden_id": garden.id,
                "bed_id": bed.id,
                "plant_id": updated_plant.id,
                "action": "update_plant",
                "resource": "plant_routes",
            },
        )
    return updated_plant


@plant_router.delete("/{plant_id}")
async def delete_bed(
    plant_id: UUID,
    service: PlantService = Depends(get_plant_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:
    """
    Route to delete a Plant

    :param plant_id: Plant UUID
    :param service: PlantService; services.plant_service.PlantService
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: dict
    """

    plant = await service.get_plant(plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    bed, _ = await plant_check_access(
        bed_id=plant.bed_id,
        user=current_user,
        enforcer=enforcer,
        action="delete",
    )

    if not await service.delete_plant(plant_id=plant_id):
        raise HTTPException(status_code=404, detail="Plant not found")

    log_handler.log_garden_event(
        event="Plant deleted",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": bed.garden_id,
            "bed_id": bed.id,
            "plant_id": plant.id,
            "action": "delete_plant",
            "resource": "plant_routes",
        },
    )

    return {"message": "Plant deleted successfully"}
