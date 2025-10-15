import uuid

import pytest
from httpx import AsyncClient

from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestUserUpdateRoutes:

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
    async def test_update_user(
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
        username = test_as.username if isinstance(test_as, User) else "Anonymous"
        payload: dict[str, str] = {
            "first_name": f"{read_user.username} updated by {username}",
        }
        response = await client.put(
            url=f"/api/users/{read_user.id}", json=payload, headers=headers
        )

        assert response.status_code == expected_status
        if expected_status == 200:
            assert (
                response.json()["first_name"]
                == f"{read_user.username} updated by {username}"
            )

    @pytest.mark.asyncio
    async def test_update_user_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        payload: dict[str, str] = {
            "first_name": "Updated by Bad ID",
        }
        response = await client.put(
            url=f"/api/users/{bad_id}", json=payload, headers=headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_update_user_self(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if hasattr(test_as, "username") else None
        headers = await get_auth_headers(client=client, user_name=username)

        payload: dict[str, str] = {
            "first_name": f"{default_user[user_name].username} updated by self",
        }
        response = await client.put(
            url=f"/api/users/{default_user[user_name].id}",
            json=payload,
            headers=headers,
        )

        assert response.status_code == expected_status
        assert (
            response.json()["first_name"]
            == f"{default_user[user_name].username} updated by self"
        )
