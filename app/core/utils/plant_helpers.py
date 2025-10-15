from uuid import UUID

from app.ai.models.ai_recommendation_model import AIRecommendations
from app.plants.recommendation_model import (
    CareInstructions,
    GrowingTips,
    Pest,
    PlantingWindow,
    Recommendations,
)


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
