import pytest
from httpx import AsyncClient

from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestUserRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
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
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
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

        read_user = default_user["authenticated"]
        response = await client.get(url=f"/api/users/{read_user.id}", headers=headers)

        assert response.status_code == expected_status
        if expected_status == 200:
            assert response.json()["username"] == read_user.username

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 403),
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

        read_user = default_user["tester"]
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
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
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

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 403),
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
            "username": f"alice+{test_as}",
            "email": f"{test_as}+alice@example.com",
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
