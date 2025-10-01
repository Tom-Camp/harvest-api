import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.ai.models.ai_recommendation_model import (
    AIRecommendations,
    CareInstructions,
    LifeCycle,
    PlantingWindow,
)
from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers

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


class TestPlantRoutes:

    @pytest.mark.asyncio
    @patch(
        "app.plants.plant_routes.get_plant_info", return_value=dummy_ai_recommendations
    )
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_create_plant(
        self,
        mock_get_plant_info: AIRecommendations,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)

        garden = default_gardens.get(user_name)
        if isinstance(garden, Garden):
            bed = garden.beds[0]
            response = await client.post(
                url="/api/plants/",
                json={
                    "species": "tomato",
                    "variety": "roma",
                    "bed_id": str(bed.id),
                },
                headers=headers,
            )
            assert response.status_code == expected_status

    @pytest.mark.asyncio
    @patch(
        "app.plants.plant_routes.get_plant_info", return_value=dummy_ai_recommendations
    )
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_read_plant(
        self,
        mock_get_plant_info: AIRecommendations,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)

        garden = default_gardens.get(user_name)
        if isinstance(garden, Garden):
            bed = garden.beds[0]
            create_response = await client.post(
                url="/api/plants/",
                json={
                    "species": "tomato",
                    "variety": "roma",
                    "bed_id": str(bed.id),
                },
                headers=headers,
            )
            plant = create_response.json()
            response = await client.get(
                url=f"/api/plants/{plant.get('id')}", headers=headers
            )
            new_plant = response.json()
            assert response.status_code == expected_status
            assert new_plant.get("species") == "tomato"

    @pytest.mark.asyncio
    async def test_read_plant_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("authenticated", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)

        bad_id = uuid.uuid4()

        response = await client.get(url=f"/api/plants/{bad_id}", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch(
        "app.plants.plant_routes.get_plant_info", return_value=dummy_ai_recommendations
    )
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 403),
            ("authenticated", 403),
        ],
    )
    async def test_update_plant(
        self,
        mock_get_plant_info: AIRecommendations,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        create_headers = await get_auth_headers(
            client=client, user_name="test_admin_user"
        )

        garden = default_gardens.get("admin")
        if isinstance(garden, Garden):
            bed = garden.beds[0]
            create_response = await client.post(
                url="/api/plants/",
                json={
                    "species": "tomato",
                    "variety": "roma",
                    "bed_id": str(bed.id),
                },
                headers=create_headers,
            )
            plant = create_response.json()
            plant_id = plant.get("id")
            test_as = default_user.get(user_name, "")
            username = test_as.username if isinstance(test_as, User) else ""
            headers = await get_auth_headers(client=client, user_name=username)
            response = await client.put(
                url=f"/api/plants/{plant_id}",
                json={"planted_date": datetime.now().isoformat()},
                headers=headers,
            )
            assert response.status_code == expected_status

    @pytest.mark.asyncio
    @patch(
        "app.plants.plant_routes.get_plant_info", return_value=dummy_ai_recommendations
    )
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_update_plant_own(
        self,
        mock_get_plant_info: AIRecommendations,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        start = datetime.now()
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)

        garden = default_gardens.get(user_name)
        if isinstance(garden, Garden):
            bed = garden.beds[0]
            create_response = await client.post(
                url="/api/plants/",
                json={
                    "species": "tomato",
                    "variety": "roma",
                    "bed_id": str(bed.id),
                },
                headers=headers,
            )
            plant = create_response.json()
            plant_id = plant.get("id")
            response = await client.put(
                url=f"/api/plants/{plant_id}",
                json={"planted_date": datetime.now().isoformat()},
                headers=headers,
            )
            updated_plant = response.json()
            assert response.status_code == expected_status
            assert datetime.fromisoformat(updated_plant.get("planted_date")) > start

    @pytest.mark.asyncio
    async def test_update_plant_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("authenticated", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)

        bad_id = uuid.uuid4()

        response = await client.put(
            url=f"/api/plants/{bad_id}",
            json={"planted_date": datetime.now().isoformat()},
            headers=headers,
        )
        assert response.status_code == 404
