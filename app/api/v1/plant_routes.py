from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.ai.plant_info_agent import get_plant_info
from app.core.auth.auth import get_current_user
from app.core.utils.database import AsyncSessionLocal, get_db
from app.core.utils.garden_helpers import check_garden_access
from app.core.utils.plant_helpers import map_ai_response_to_plant
from app.logging import get_logger, log_handler
from app.models.bed_models import Bed
from app.models.garden_models import Garden
from app.models.plant_models import Plant
from app.schemas.auth_schemas import TokenData
from app.schemas.plant_schemas import PlantCreate, PlantRead, PlantUpdate
from app.services.plant_service import PlantService

logger = get_logger(__name__)

plant_router = APIRouter(prefix="/plants")


def get_plant_service() -> PlantService:
    return PlantService(session=AsyncSessionLocal())


@plant_router.post("/", response_model=Plant)
async def create_plant(
    plant: PlantCreate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: PlantService = Depends(get_plant_service),
    session: AsyncSession = Depends(get_db),
) -> Plant:
    """
    Create a Plant object

    :param plant: a PlantCreate object; schemas.plant_schema.PlantCreate
    :param current_user: User object for the user accessing the route.
    :param service: PlantService; services.plant_service.PlantService
    :param session: SQLAlchemy asyncio AsyncSession
    :return: Plant object; plants.plant_models.Plant
    """

    statement = (
        select(Garden.user_id, Garden.id, Garden.location, Bed.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .where(Bed.id == plant.bed_id)
    )
    garden_user, garden_id, location, bed_id = session.execute(statement).first()

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:up"
    )

    new_plant = await service.create_plant(plant=plant)
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
            "garden_id": garden_id,
            "bed_id": bed_id,
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
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    service: PlantService = Depends(get_plant_service),
    session: AsyncSession = Depends(get_db),
) -> PlantRead:
    """
    Return a PlantRead object by the Plant ID

    :param plant_id: Unique ID for the plant
    :param current_user: User object for the user accessing the route.
    :param service: PlantService; services.plant_service.PlantService
    :param session: SQLAlchemy asyncio AsyncSession
    :return: PlantRead object; plants.plant_schemas.PlantRead
    """

    plant = await service.get_plant(plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    statement = (
        select(Garden.user_id)
        .join(Bed, Garden.id == Bed.garden_id)
        .where(Bed.id == plant.bed_id)
    )
    garden_user = session.execute(statement).first()

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:re"
    )

    return plant


@plant_router.put("/{plant_id}", response_model=PlantRead)
async def update_plant(
    plant_id: UUID,
    plant_update: PlantUpdate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: PlantService = Depends(get_plant_service),
    session: AsyncSession = Depends(get_db),
) -> Plant | None:
    """
    A route for updating a Plant object

    :param plant_id: the Plant unique ID
    :param plant_update: a PlantUpdate object; plants.plant_schemas.PlantUpdate
    :param current_user: the User making the request
    :param service: PlantService; services.plant_service.PlantService
    :param session: SQLAlchemy asnycio AsyncSession
    :return: PlantRead object; plants.plant_schemas.PlantRead
    """

    plant = await service.get_plant(plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    statement = (
        select(Garden.id, Garden.user_id, Garden.location, Bed.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .where(Bed.id == plant.bed_id)
    )
    garden_id, garden_user, location, bed_id = session.execute(statement).first()

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:up"
    )

    updated_plant = await service.update_plant(
        plant_id=plant_id, plant_update=plant_update
    )

    if (
        updated_plant
        and hasattr(updated_plant, "variety")
        and updated_plant.variety != plant.variety
    ):
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
                "garden_id": garden_id,
                "bed_id": bed_id,
                "plant_id": updated_plant.id,
                "action": "update_plant",
                "resource": "plant_routes",
            },
        )
    return updated_plant


@plant_router.delete("/{plant_id}")
async def delete_bed(
    plant_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:de", "ga:de:own"])
    ],
    service: PlantService = Depends(get_plant_service),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Route to delete a Plant

    :param plant_id: Plant UUID
    :param current_user: User
    :param service: PlantService; services.plant_service.PlantService
    :param session: SQLAlchemy asyncio AsyncSession
    :return: dict
    """

    plant = await service.get_plant(plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    statement = (
        select(Garden.id, Garden.user_id, Garden.location, Bed.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .where(Bed.id == plant.bed_id)
    )
    garden_id, garden_user, location, bed_id = session.execute(statement).first()

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:de"
    )

    if not await service.delete_plant(plant_id=plant_id):
        raise HTTPException(status_code=404, detail="Plant not found")

    log_handler.log_garden_event(
        event="Plant deleted",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": garden_id,
            "bed_id": bed_id,
            "plant_id": plant.id,
            "action": "delete_plant",
            "resource": "plant_routes",
        },
    )

    return {"message": "Plant deleted successfully"}
