# test_auth_routes.py
import logging
import uuid

import pytest

pytestmark = pytest.mark.asyncio


class TestAuthRoutes:
    header: dict[str, str] = {"Content-Type": "application/json"}
    username: str = f"testuser_{uuid.uuid4().hex[:8]}"
    email: str = f"{username}@example.com"
    password: str = "StrongPass!123"

    @staticmethod
    async def test_health(client):
        health_response = await client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json() == {"status": "healthy"}

    async def test_register(self, client):
        register_response = await client.post(
            "/api/auth/register",
            json={
                "username": self.username,
                "email": self.email,
                "password": self.password,
            },
            headers=self.header,
        )
        assert register_response.status_code == 200, register_response.text
        assert register_response.json()["username"] == self.username

    async def test_login(self, client):
        login_response = await client.post(
            "/api/auth/token",
            data={
                "username": self.username,
                "password": self.password,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        logging.debug("LOGIN RESP: %s" % login_response)
        assert login_response.status_code == 200, login_response.text
        token = login_response.json()
        assert "access_token" in token
        assert token["token_type"] == "bearer"

    async def test_admin_login(self, client):
        from app.utils.config import settings

        admin_response = await client.post(
            "/api/auth/token",
            data={
                "username": settings.INITIAL_USER_NAME,
                "password": settings.INITIAL_USER_PASS,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        logging.debug("ADMIN RESP: %s" % admin_response)
        assert admin_response.status_code == 200, admin_response.text
        token = admin_response.json()
        assert "access_token" in token
        assert token["token_type"] == "bearer"
