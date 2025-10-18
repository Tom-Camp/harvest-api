import uuid

import pytest
from httpx import AsyncClient

from app.models.garden_models import Garden
from app.models.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestGardenNoteDeleteRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_delete_garden_note(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        create_as = default_user.get(user_name, "")
        username = create_as.username if isinstance(create_as, User) else ""
        create_headers = await get_auth_headers(client=client, user_name=username)
        garden = default_gardens.get(user_name)
        if isinstance(garden, Garden):
            create_response = await client.post(
                url="/api/garden-notes/",
                json={"note": "My new garden note", "garden_id": str(garden.id)},
                headers=create_headers,
            )
            note = create_response.json()

            test_as = default_user.get(user_name, "")
            username = test_as.username if isinstance(test_as, User) else ""
            headers = await get_auth_headers(client=client, user_name=username)

            delete_note = await client.delete(
                url=f"/api/garden-notes/{note.get('id')}", headers=headers
            )
            assert delete_note.status_code == expected_status

        else:
            pytest.fail("No garden found for user test_user")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("test_admin", 200),
            ("test_moderator", 403),
            ("test_authenticated", 403),
        ],
    )
    async def test_delete_garden_note_any(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        create_as = default_user.get("test_user", "")
        username = create_as.username if isinstance(create_as, User) else ""
        create_headers = await get_auth_headers(client=client, user_name=username)
        garden = default_gardens.get("test_user")
        if isinstance(garden, Garden):
            create_response = await client.post(
                url="/api/garden-notes/",
                json={"note": "My new garden note", "garden_id": str(garden.id)},
                headers=create_headers,
            )
            note = create_response.json()

            test_as = default_user.get(user_name, "")
            username = test_as.username if isinstance(test_as, User) else ""
            headers = await get_auth_headers(client=client, user_name=username)

            delete_note = await client.delete(
                url=f"/api/garden-notes/{note.get('id')}", headers=headers
            )
            assert delete_note.status_code == expected_status

        else:
            pytest.fail("No garden found for user test_user")

    @pytest.mark.asyncio
    async def test_delete_garden_note_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.delete(
            url=f"/api/garden-notes/{bad_id}", headers=headers
        )
        assert response.status_code == 404
