from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.ai.models.ai_recommendation_model import AIRecommendations
from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import (
    create_note,
    create_plant,
    dummy_ai_recommendations,
    get_auth_headers,
)


class TestPlantNotesDeleteRoutes:
    note_json: dict = {"note": "this is a plant note", "plant_id": ""}
    note_url: str = "/api/plant-notes/"

    @pytest.mark.asyncio
    @patch(
        "app.plants.plant_routes.get_plant_info", return_value=dummy_ai_recommendations
    )
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("test_admin", 200),
            ("test_moderator", 403),
            ("test_authenticated", 403),
        ],
    )
    async def test_delete_plant_note(
        self,
        mock_get_plant_info: AIRecommendations,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get("test_user", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)

        garden = default_gardens.get("test_user")
        if isinstance(garden, Garden):
            bed = garden.beds[0]
            plant = await create_plant(
                client=client, bed_id=str(bed.id), headers=headers
            )
            self.note_json["plant_id"] = plant.get("id")
            note = await create_note(
                client=client,
                note=self.note_json,
                url=self.note_url,
                headers=headers,
            )

            test_as = default_user.get(user_name, "")
            username = test_as.username if isinstance(test_as, User) else ""
            get_headers = await get_auth_headers(client=client, user_name=username)
            get_response = await client.delete(
                url=f"/api/plant-notes/{note.get('id')}",
                headers=get_headers,
            )
            if get_response.status_code == 200:
                note = get_response.json()
                assert note.get("message") == "Note deleted successfully"
        else:
            pytest.fail(f"No garden found for user {username}")
