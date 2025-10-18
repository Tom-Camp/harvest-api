import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models.ai_recommendation_model import AIRecommendations
from app.models.garden_models import Garden
from app.models.user_models import User
from tests.helpers.test_helpers import (
    create_bed,
    create_note,
    create_plant,
    dummy_ai_recommendations,
    get_auth_headers,
)


class TestPlantNotesReadRoutes:
    note_json: dict = {"note": "this is a plant note", "plant_id": ""}
    note_url: str = "/api/plant-notes/"

    @pytest.mark.asyncio
    @patch(
        "app.api.v1.plant_routes.get_plant_info", return_value=dummy_ai_recommendations
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
    async def test_read_plant_note(
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
            new_bed = await create_bed(
                client=client, garden_id=str(garden.id), headers=headers
            )
            plant = await create_plant(
                client=client, bed_id=new_bed.get("id", ""), headers=headers
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

        garden = default_gardens.get("test_user")
        if isinstance(garden, Garden):
            new_bed = await create_bed(
                client=client, garden_id=str(garden.id), headers=headers
            )
            plant = await create_plant(
                client=client, bed_id=new_bed.get("id", ""), headers=headers
            )
            self.note_json["plant_id"] = plant.get("id")
            note = await create_note(
                client=client,
                note=self.note_json,
                url=self.note_url,
                headers=headers,
            )
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
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(
            url=f"/api/bed-notes/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch(
        "app.api.v1.plant_routes.get_plant_info", return_value=dummy_ai_recommendations
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
    async def test_read_plant_notes(
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
            new_bed = await create_bed(
                client=client, garden_id=str(garden.id), headers=headers
            )
            plant = await create_plant(
                client=client, bed_id=new_bed.get("id", ""), headers=headers
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

            get_response = await client.get(
                url=f"/api/plant-notes/notes/{plant.get('id')}",
                headers=get_headers,
            )
            if get_response.status_code == 200:
                note = get_response.json()
                assert isinstance(note, list)
        else:
            pytest.fail(f"No garden found for user {username}")

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
    async def test_read_plant_notes_own(
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

        garden = default_gardens.get("test_user")
        if isinstance(garden, Garden):
            new_bed = await create_bed(
                client=client, garden_id=str(garden.id), headers=headers
            )
            plant = await create_plant(
                client=client, bed_id=new_bed.get("id", ""), headers=headers
            )
            self.note_json["plant_id"] = plant.get("id")
            note = await create_note(
                client=client,
                note=self.note_json,
                url=self.note_url,
                headers=headers,
            )

            get_response = await client.get(
                url=f"/api/plant-notes/notes/{plant.get('id')}",
                headers=headers,
            )
            if get_response.status_code == 200:
                note = get_response.json()
                assert isinstance(note, list)
        else:
            pytest.fail(f"No garden found for user {username}")

    @pytest.mark.asyncio
    async def test_read_plant_notes_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(
            url=f"/api/plant-notes/notes/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404
