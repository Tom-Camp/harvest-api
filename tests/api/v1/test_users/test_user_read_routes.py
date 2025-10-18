import uuid

import pytest
from httpx import AsyncClient

from app.models.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestUserRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_read_users_me(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        response = await client.get(url="/api/users/me", headers=headers)

        assert response.status_code == expected_status
        if isinstance(test_as, User):
            assert response.json()["username"] == test_as.username

    @pytest.mark.asyncio
    async def test_read_users(self, client: AsyncClient):
        response = await client.get(url="/api/users/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 403),
        ],
    )
    async def test_read_user(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if hasattr(test_as, "username") else None
        headers = await get_auth_headers(client=client, user_name=username)

        read_user = default_user["test_user"]
        response = await client.get(url=f"/api/users/{read_user.id}", headers=headers)

        assert response.status_code == expected_status
        if expected_status == 200:
            assert response.json()["username"] == read_user.username

    @pytest.mark.asyncio
    async def test_read_user_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_moderator", "")
        username = test_as.username if hasattr(test_as, "username") else None
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(url=f"/api/users/{bad_id}", headers=headers)
        assert response.status_code == 404
