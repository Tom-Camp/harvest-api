import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.ai.models.ai_recommendation_model import AIRecommendations
from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import (
    create_plant,
    dummy_ai_recommendations,
    get_auth_headers,
)


class TestPlantReadRoutes:

    @pytest.mark.asyncio
    @patch(
        "app.plants.plant_routes.get_plant_info", return_value=dummy_ai_recommendations
    )
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
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
            plant = await create_plant(
                client=client, bed_id=str(bed.id), headers=headers
            )
            response = await client.get(
                url=f"/api/plants/{plant.get('id')}", headers=headers
            )
            new_plant = response.json()
            assert response.status_code == expected_status
            assert new_plant.get("species") == "tomato"
        else:
            pytest.fail(f"No garden found for user {username}")

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
    async def test_read_plant_unauthenticated(
        self,
        mock_get_plant_info: AIRecommendations,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
    ):
        test_as = default_user.get("tester", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)

        garden = default_gardens.get("tester")
        if isinstance(garden, Garden):
            bed = garden.beds[0]
            plant = await create_plant(
                client=client, bed_id=str(bed.id), headers=headers
            )
            plant_id = plant.get("id")
            new_headers = await get_auth_headers(client=client, user_name="")
            response = await client.get(
                url=f"/api/plants/{plant_id}", headers=new_headers
            )

            assert response.status_code == 401
        else:
            pytest.fail("No garden found for user tester")
