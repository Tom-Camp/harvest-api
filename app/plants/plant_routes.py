from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.plant_info_agent import get_plant_info
from app.auth.auth import get_current_active_user
from app.beds.bed_models import Bed
from app.core.utils.plant_helpers import map_ai_response_to_plant
from app.gardens.garden_models import Garden
from app.logging import get_logger, log_handler
from app.plants.plant_crud import PlantCRUD
from app.plants.plant_models import Plant
from app.plants.plant_schemas import PlantCreate, PlantRead, PlantUpdate
from app.users.user_models import User
from app.utils.database import get_db

logger = get_logger(__name__)

plant_router = APIRouter(prefix="/plants")


@plant_router.post("/", response_model=Plant)
async def create_plant(
    plant: PlantCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Plant:
    """
    Create a Plant object

    :param plant: a PlantCreate object; plants.plant_schema.PlantCreate
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User object for the user accessing the route.
    :return: Plant object; plants.plant_models.Plant
    """

    new_plant = await PlantCRUD.create_plant(plant=plant, session=session)
    bed = await session.get(Bed, new_plant.bed_id)
    garden = await session.get(Garden, bed.garden_id)
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
            # "garden_id": bed.garden_id,
            # "bed_id": bed.id,
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
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PlantRead:
    """
    Return a PlantRead object by the Plant ID

    :param plant_id: Unique ID for the plant
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User object for the user accessing the route.
    :return: PlantRead object; plants.plant_schemas.PlantRead
    """

    plant = await PlantCRUD.get_plant(session=session, plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    return plant


@plant_router.put("/{plant_id}", response_model=PlantRead)
async def update_plant(
    plant_id: UUID,
    plant_update: PlantUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Plant | None:
    """
    A route for updating a Plant object

    :param plant_id: the Plant unique ID
    :param plant_update: a PlantUpdate object; plants.plant_schemas.PlantUpdate
    :param session: SQLAlchemy asnycio AsyncSession
    :param current_user: the User making the request
    :return: PlantRead object; plants.plant_schemas.PlantRead
    """

    plant = await PlantCRUD.get_plant(session=session, plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    updated_plant = await PlantCRUD.update_plant(
        session=session, plant_id=plant_id, plant_update=plant_update
    )
    bed = await session.get(Bed, plant.bed_id)
    garden = await session.get(
        Garden,
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
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Route to delete a Plant

    :param plant_id: Plant UUID
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: dict
    """

    plant = await PlantCRUD.get_plant(session=session, plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    if not await PlantCRUD.delete_plant(session, plant_id):
        raise HTTPException(status_code=404, detail="Plant not found")

    log_handler.log_garden_event(
        event="Plant deleted",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            # "garden_id": bed.garden_id,
            # "bed_id": bed.id,
            "plant_id": plant.id,
            "action": "delete_plant",
            "resource": "plant_routes",
        },
    )

    return {"message": "Plant deleted successfully"}
