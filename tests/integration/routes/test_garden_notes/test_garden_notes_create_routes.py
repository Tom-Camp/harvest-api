import uuid

import pytest
from httpx import AsyncClient

from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestGardenNoteCreateRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_create_garden_note(
        self,
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
            garden_id = garden.id
            response = await client.post(
                url="/api/garden-notes/",
                json={"note": "this is the first note", "garden_id": str(garden_id)},
                headers=headers,
            )
            data = response.json()
            assert response.status_code == expected_status
            assert data.get("note") == "this is the first note"
        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_create_garden_note_unauthenticated(
        self,
        client: AsyncClient,
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("tester")
        if isinstance(garden, Garden):
            response = await client.post(
                url="/api/garden-notes/",
                json={"note": "this is the first note", "garden_id": str(garden.id)},
                headers=headers,
            )
            assert response.status_code == 401
        else:
            pytest.fail("No garden found for user test_user")

    @pytest.mark.asyncio
    async def test_create_garden_note_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.post(
            url="/api/garden-notes/",
            json={"note": "this is the first note", "garden_id": str(bad_id)},
            headers=headers,
        )
        assert response.status_code == 404
