from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.ai.models.ai_recommendation_model import AIRecommendations
from app.beds.bed_crud import BedCRUD
from app.beds.bed_schemas import BedRead
from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.gardens.garden_crud import GardenCRUD
from app.gardens.garden_models import Garden
from app.plants.recommendation_model import (
    CareInstructions,
    GrowingTips,
    Pest,
    PlantingWindow,
    Recommendations,
)
from app.users.user_models import User


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


async def plant_check_access(
    bed_id: UUID,
    user: User,
    session: AsyncSession,
    enforcer: AsyncEnforcer,
    action: str,
) -> tuple[BedRead, Garden]:
    """
    Access control function for plant routes

    :param bed_id: The unique ID for the bed that the plant is associated with
    :param user: the User object for the user accessing the route; users.users_models.User
    :param session: SQLAlchemy asyncio AsyncSession
    :param enforcer: Casbin enforcer
    :param action: The action for the enforcer to check; create, read, update, delete
    :return: Return the BedRead and Garden objects
    """

    bed = await BedCRUD.get_bed(session=session, bed_id=bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Garden not found")

    user_subject: str = casbin_subject(user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, action)

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    return bed, garden
