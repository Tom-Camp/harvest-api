from typing import Dict

from httpx import AsyncClient

from app.ai.models.ai_recommendation_model import (
    AIRecommendations,
    CareInstructions,
    LifeCycle,
    PlantingWindow,
)

dummy_ai_recommendations = AIRecommendations(
    life_cycle=LifeCycle.ANNUAL,
    days_to_harvest=60,
    companion_plants="basil",
    growing_tips=[],
    planting_window=PlantingWindow(
        season="winter",
        temperature_range="70 to 80 degrees",
    ),
    care_instructions=CareInstructions(
        watering_frequency="daily",
        sunlight_needs="full sun",
        soil_type="loam",
    ),
    pests=[],
)


async def get_auth_headers(
    client: AsyncClient, user_name: str | None
) -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if user_name:
        get_token = await client.post(
            url="/api/auth/token",
            data={"username": user_name, "password": "UkeV3BNUIL7x/n0J"},
        )
        headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
    return headers


async def create_plant(client: AsyncClient, bed_id: str, headers: dict):
    response = await client.post(
        url="/api/plants/",
        json={
            "species": "tomato",
            "variety": "roma",
            "bed_id": bed_id,
        },
        headers=headers,
    )
    return response.json()


async def create_note(client, url, note, headers):
    response = await client.post(
        url=url,
        json=note,
        headers=headers,
    )
    return response.json()
