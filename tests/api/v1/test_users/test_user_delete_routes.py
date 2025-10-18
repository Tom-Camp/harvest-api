import uuid

import pytest
from httpx import AsyncClient

from app.models.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestUserDeleteRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 403),
            ("test_authenticated", 403),
        ],
    )
    async def test_delete_user(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if hasattr(test_as, "username") else None
        headers = await get_auth_headers(client=client, user_name=username)

        payload = {
            "username": f"alice+{user_name}",
            "email": f"{user_name}+alice@example.com",
            "password": "milk prairie island desert",
        }
        response = await client.post(
            url="/api/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        delete_user = response.json()
        delete_response = await client.delete(
            url=f"/api/users/{delete_user.get('id', '')}",
            headers=headers,
        )
        assert delete_response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_delete_user_unauthenticated(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        user = default_user.get("test_user")
        if isinstance(user, User):
            response = await client.delete(
                url=f"/api/users/{user.id}",
                headers=headers,
            )
            assert response.status_code == 401
        else:
            pytest.fail("No user found for user test_user")

    @pytest.mark.asyncio
    async def test_delete_user_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.delete(
            url=f"/api/users/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404
