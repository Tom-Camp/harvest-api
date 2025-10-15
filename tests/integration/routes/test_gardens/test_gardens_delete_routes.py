import uuid

import pytest
from httpx import AsyncClient

from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestGardenDeleteRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 403),
            ("test_authenticated", 403),
        ],
    )
    async def test_delete_garden(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        create_as = default_user.get("test_user", "")
        username = create_as.username if isinstance(create_as, User) else ""
        create_headers = await get_auth_headers(client=client, user_name=username)
        create_response = await client.post(
            url="/api/gardens/",
            json={
                "name": "My new garden",
                "description": "This is the garden",
                "location": "Delta, Colorado",
            },
            headers=create_headers,
        )
        garden_id = create_response.json()

        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        delete_garden = await client.delete(
            url=f"/api/gardens/{garden_id.get('id')}", headers=headers
        )
        assert delete_garden.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_delete_garden_own(
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
            delete_garden = await client.delete(
                url=f"/api/gardens/{garden.id}", headers=headers
            )
            assert delete_garden.status_code == expected_status
        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_delete_garden_unauthenticated(
        self,
        client: AsyncClient,
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("test_user")
        if isinstance(garden, Garden):
            response = await client.delete(
                url=f"/api/gardens/{garden.id}",
                headers=headers,
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_garden_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.delete(
            url=f"/api/gardens/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404
