from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models.ai_recommendation_model import AIRecommendations
from app.ai.plant_info_agent import get_plant_info
from app.auth.auth import get_current_active_user
from app.beds.bed_crud import BedCRUD
from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.gardens.garden_crud import GardenCRUD
from app.logging import get_logger, log_handler
from app.plants.plant_crud import PlantCRUD
from app.plants.plant_models import Plant
from app.plants.plant_schema import PlantCreate, PlantRead, PlantUpdate
from app.plants.recommendation_model import (
    CareInstructions,
    GrowingTips,
    Pest,
    PlantingWindow,
    Recommendations,
)
from app.users.user_models import User
from app.utils.database import get_db

logger = get_logger(__name__)

plant_router = APIRouter(prefix="/plants")


async def map_ai_response_to_plant(
    plant_id: UUID, ai_recommendations: AIRecommendations
) -> Recommendations:
    """
    Map the AIRecommendation object to the Plant Recommendations model.

    :param plant_id: The unique ID for the plant
    :param ai_recommendations: The AIRecommendations object; ai.modes.ai_recommendations.AIRecommendations
    :return: Recommendations object; plants.recommendations_model.Recommendations
    """
    growing_tips = [
        GrowingTips(tips=tip.tips) for tip in ai_recommendations.growing_tips
    ]
    pests = [Pest(pest=pest.pest) for pest in (ai_recommendations.pests or [])]
    planting_window = PlantingWindow(
        season=ai_recommendations.planting_window.season,
        months=ai_recommendations.planting_window.months,
        temperature_range=ai_recommendations.planting_window.temperature_range,
    )
    care_instructions = CareInstructions(
        watering_frequency=ai_recommendations.care_instructions.watering_frequency,
        sunlight_needs=ai_recommendations.care_instructions.sunlight_needs,
        soil_type=ai_recommendations.care_instructions.soil_type,
        spacing=ai_recommendations.care_instructions.spacing,
    )
    recommendations = Recommendations(
        life_cycle=ai_recommendations.life_cycle,
        days_to_harvest=ai_recommendations.days_to_harvest,
        companion_plants=ai_recommendations.companion_plants,
        growing_tips=growing_tips,
        planting_window=planting_window,
        care_instructions=care_instructions,
        pests=pests,
        plant_id=plant_id,
    )
    return recommendations


@plant_router.post("/", response_model=Plant)
async def create_plant(
    plant: PlantCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Plant:
    """
    Create a Plant object

    :param plant: a PlantCreate object; plants.plant_schema.PlantCreate
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User object for the user accessing the route.
    :param enforcer: Casbin AsyncEnforcer
    :return: Plant object; plants.plant_models.Plant
    """

    bed = await BedCRUD.get_bed(session=session, bed_id=plant.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed Not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "create")

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    new_plant = await PlantCRUD.create_plant(plant=plant, session=session)
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
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> PlantRead:
    """
    Return a PlantRead object by the Plant ID

    :param plant_id: Unique ID for the plant
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User object for the user accessing the route.
    :param enforcer: Casbin AsyncEnforcer
    :return: PlantRead object; plants.plant_schemas.PlantRead
    """

    plant = await PlantCRUD.get_plant(session=session, plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    bed = await BedCRUD.get_bed(session=session, bed_id=plant.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Garden not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "read")

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    return plant


@plant_router.put("/{plant_id}", response_model=PlantRead)
async def update_plant(
    plant_id: UUID,
    plant_update: PlantUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Plant | None:
    """
    A route for updating a Plant object

    :param plant_id: the Plant unique ID
    :param plant_update: a PlantUpdate object; plants.plant_schemas.PlantUpdate
    :param session: SQLAlchemy asnycio AsyncSession
    :param current_user: the User making the request
    :param enforcer: Casbin AsyncEnforcer
    :return: PlantRead object; plants.plant_schemas.PlantRead
    """

    plant = await PlantCRUD.get_plant(session=session, plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    bed = await BedCRUD.get_bed(session=session, bed_id=plant.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    user_subject = casbin_subject(current_user.id)
    garden_resource = casbin_object("ga", bed.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "update")

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    updated_plant = await PlantCRUD.update_plant(
        session=session, plant_id=plant_id, plant_update=plant_update
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
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:
    """
    Route to delete a Plant

    :param plant_id: Plant UUID
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :param enforcer: Casbin AsyncEnforcer
    :return: dict
    """

    plant = await PlantCRUD.get_plant(session=session, plant_id=plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    bed = await BedCRUD.get_bed(session=session, bed_id=plant.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    user_subject = casbin_subject(current_user.id)
    garden_resource = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, "delete")

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not await PlantCRUD.delete_plant(session, plant_id):
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
