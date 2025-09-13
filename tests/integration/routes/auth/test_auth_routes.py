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
    async def test_user_login(self, client, default_user):
        payload: dict = {
            "username": "testuser",
            "password": "Passw0rd!123",
        }
        response = await client.post(
            "/api/auth/token",
            data=payload,
        )
        assert "access_token" in response.json()
