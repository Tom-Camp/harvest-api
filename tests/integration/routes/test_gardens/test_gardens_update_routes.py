import uuid

import pytest
from httpx import AsyncClient

from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestGardenUpdateRoutes:

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
    async def test_update_garden(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):

        garden = default_gardens.get("test_user")
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        if isinstance(garden, Garden):
            response = await client.put(
                url=f"/api/gardens/{garden.id}",
                json={
                    "name": f"{username}'s updated garden",
                    "description": "This has been Updated",
                },
                headers=headers,
            )
            assert response.status_code == expected_status
            if response.status_code == 200:
                assert response.json()["name"] == f"{username}'s updated garden"
        else:
            pytest.fail("No garden found for user test_user")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_update_garden_own(
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
        update_garden = default_gardens.get(user_name, "")
        if isinstance(update_garden, Garden):
            response = await client.put(
                url=f"/api/gardens/{update_garden.id}",
                json={
                    "name": f"{user_name}'s updated garden",
                    "description": "This has been Updated",
                },
                headers=headers,
            )
            assert response.status_code == expected_status
            assert response.json()["name"] == f"{user_name}'s updated garden"
        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_update_garden_unauthenticated(
        self,
        client: AsyncClient,
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("test_user")
        if isinstance(garden, Garden):
            response = await client.put(
                url=f"/api/gardens/{garden.id}",
                json={
                    "name": "Unauthenticated's updated garden",
                    "description": "This has been Updated",
                },
                headers=headers,
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_garden_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.put(
            url=f"/api/gardens/{bad_id}",
            json={
                "name": "Bad ID's updated garden",
                "description": "This has been Updated",
            },
            headers=headers,
        )
        assert response.status_code == 404
