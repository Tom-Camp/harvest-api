import pytest


class TestUserRoutes:

    @pytest.mark.asyncio
    async def test_user_register(self, client):
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
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"

    @pytest.mark.asyncio
    async def test_user_register_invalid_email(self, client):
        payload: dict = {
            "username": "alice",
            "email": "alice@example",
            "password": "secret123",
        }
        response = await client.post(
            "/api/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_user_register_invalid_username(self, client):
        payload: dict = {
            "email": "alice@example",
            "password": "secret123",
        }
        response = await client.post(
            "/api/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_user_login(self, client, default_user):
        user = default_user.get("user")
        payload: dict = {
            "username": user.username,
            "password": "Passw0rd!123",
        }
        response = await client.post(
            "/api/auth/token",
            data=payload,
        )
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_user_login_invalid_password(self, client, default_user):
        user = default_user.get("user")
        payload: dict = {
            "username": user.username,
            "password": "Passw0rd!1234",
        }
        response = await client.post(
            "/api/auth/token",
            data=payload,
        )
        assert response.status_code == 401
        assert response.json().get("detail", "") == "Incorrect username or password"
