from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models.ai_recommendation_model import AIRecommendations
from app.models.garden_models import Garden
from app.models.user_models import User
from tests.helpers.test_helpers import (
    create_bed,
    dummy_ai_recommendations,
    get_auth_headers,
)


class TestPlantCreateRoutes:

    @pytest.mark.asyncio
    @patch(
        "app.api.v1.plant_routes.get_plant_info", return_value=dummy_ai_recommendations
    )
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
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
            new_bed = await create_bed(
                client=client, garden_id=str(garden.id), headers=headers
            )
            response = await client.post(
                url="/api/plants/",
                json={
                    "species": "tomato",
                    "variety": "roma",
                    "bed_id": str(new_bed.get("id", None)),
                },
                headers=headers,
            )
            assert response.status_code == expected_status
        else:
            pytest.fail(f"No garden found for user {username}")
