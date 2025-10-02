import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.ai.models.ai_recommendation_model import AIRecommendations
from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import dummy_ai_recommendations, get_auth_headers


class TestPlantReadRoutes:

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
    async def test_read_plant_note(
        self,
        mock_get_plant_info: AIRecommendations,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get("tester", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)

        garden = default_gardens.get("tester")
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
            note_response = await client.post(
                url="/api/plant-notes/",
                json={"note": "this is a plant note", "plant_id": str(plant_id)},
                headers=headers,
            )
            note = note_response.json()

            test_as = default_user.get(user_name, "")
            username = test_as.username if isinstance(test_as, User) else ""
            get_headers = await get_auth_headers(client=client, user_name=username)
            get_response = await client.get(
                url=f"/api/plant-notes/{note.get('id')}",
                headers=get_headers,
            )
            if get_response.status_code == 200:
                note = get_response.json()
                assert note.get("note") == "this is a plant note"
        else:
            pytest.fail(f"No garden found for user {username}")

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
    async def test_read_plant_note_own(
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

        garden = default_gardens.get("tester")
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
            note_response = await client.post(
                url="/api/plant-notes/",
                json={"note": "this is a plant note", "plant_id": str(plant_id)},
                headers=headers,
            )
            note = note_response.json()
            get_response = await client.get(
                url=f"/api/plant-notes/{note.get('id')}",
                headers=headers,
            )
            if get_response.status_code == 200:
                note = get_response.json()
                assert note.get("note") == "this is a plant note"
        else:
            pytest.fail(f"No garden found for user {username}")

    @pytest.mark.asyncio
    async def test_read_plant_note_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(
            url=f"/api/bed-notes/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404
