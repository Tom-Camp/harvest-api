from typing import Dict, List

import pytest

from app.users.user_models import User


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
        self, client, default_user, user_name, expected_status
    ):
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        response = await client.get(url="/api/users/me", headers=headers)

        assert response.status_code == expected_status
        if response.status_code == 200:
            assert response.json()["username"] == test_as.username

    @pytest.mark.asyncio
    async def test_read_users(self, client):
        response = await client.get(url="/api/users/")

        assert response.status_code == 200
        assert isinstance(response.json(), List)

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
        self, client, default_user, user_name: str, expected_status: int
    ):
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"

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
        self, client, default_user, user_name: str, expected_status: int
    ):
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"

        read_user = default_user["tester"]
        username = test_as.username if isinstance(test_as, User) else "Anonymous"
        payload: Dict[str, str] = {
            "full_name": f"{read_user.username} updated by {username}",
        }
        response = await client.put(
            url=f"/api/users/{read_user.id}", json=payload, headers=headers
        )

        assert response.status_code == expected_status
        if expected_status == 200:
            assert (
                response.json()["full_name"]
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
        self, client, default_user, user_name: str, expected_status: int
    ):
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        get_token = await client.post(
            url="/api/auth/token",
            data={
                "username": default_user[user_name].username,
                "password": "UkeV3BNUIL7x/n0J",
            },
        )
        headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"

        payload: Dict[str, str] = {
            "full_name": f"{default_user[user_name].username} updated by self",
        }
        response = await client.put(
            url=f"/api/users/{default_user[user_name].id}",
            json=payload,
            headers=headers,
        )

        assert response.status_code == expected_status
        assert (
            response.json()["full_name"]
            == f"{default_user[user_name].username} updated by self"
        )
