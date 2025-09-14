from typing import List

import pytest


class TestUserRoutes:
    headers: dict = {"Content-Type": "application/json"}

    @pytest.mark.asyncio
    async def test_read_users_me(self, client, default_user):
        test_as = next(iter(default_user.values()))
        get_token = await client.post(
            url="/api/auth/token",
            data={"username": test_as.username, "password": "Passw0rd!123"},
        )
        self.headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        response = await client.get(url="/api/users/me", headers=self.headers)

        assert response.status_code == 200
        assert response.json()["username"] == test_as.username

    @pytest.mark.asyncio
    async def test_read_users(self, client):
        response = await client.get(url="/api/users/")

        assert response.status_code == 200
        assert isinstance(response.json(), List)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_user,expected_status",
        [
            ("admin", 200),
            ("moderator", 403),
            ("user", 403),
        ],
    )
    async def test_read_user(
        self, client, default_user, test_user: str, expected_status: int
    ):
        test_as = default_user[test_user]
        read_user = default_user["user"]
        get_token = await client.post(
            url="/api/auth/token",
            data={"username": test_as.username, "password": "Passw0rd!123"},
        )
        self.headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        response = await client.get(
            url=f"/api/users/{read_user.id}", headers=self.headers
        )

        assert response.status_code == expected_status
        if expected_status == 200:
            assert response.json()["username"] == read_user.username

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_user,expected_status",
        [
            ("admin", 200),
            ("moderator", 403),
            ("user", 403),
        ],
    )
    async def test_update_user(
        self, client, default_user, test_user: str, expected_status: int
    ):
        test_as = default_user[test_user]
        read_user = default_user["user"]
        get_token = await client.post(
            url="/api/auth/token",
            data={"username": test_as.username, "password": "Passw0rd!123"},
        )
        self.headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        payload: dict = {
            "full_name": f"Updated by {test_as.username}",
        }
        response = await client.put(
            url=f"/api/users/{read_user.id}", json=payload, headers=self.headers
        )

        assert response.status_code == expected_status
        if expected_status == 200:
            assert response.json()["full_name"] == f"Updated by {test_as.username}"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_user,expected_status",
        [
            ("admin", 200),
            ("moderator", 403),
            ("user", 403),
        ],
    )
    async def test_delete_user(
        self, client, default_user, test_user: str, expected_status: int
    ):
        test_as = default_user[test_user]
        get_token = await client.post(
            url="/api/auth/token",
            data={"username": test_as.username, "password": "Passw0rd!123"},
        )
        self.headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        payload: dict = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
        }
        response = await client.post(
            "/api/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        new_user = response.json()
        response = await client.delete(
            url=f"/api/users/{new_user.get('id', None)}", headers=self.headers
        )

        assert response.status_code == expected_status
        if expected_status == 200:
            assert response.json().get("message") == "User alice deleted successfully"
