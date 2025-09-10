# test_auth_routes.py
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
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "healthy"}

    async def test_register_and_login(self, client):
        r = await client.post(
            "/api/auth/register",
            json={
                "username": self.username,
                "email": self.email,
                "password": self.password,
            },
            headers=self.header,
        )
        assert r.status_code == 200, r.text
        assert r.json()["username"] == self.username

    async def test_login(self, client):
        r2 = await client.post(
            "/api/auth/token",
            data={
                "username": self.username,
                "password": self.password,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r2.status_code == 200, r2.text
        token = r2.json()
        assert "access_token" in token
        assert token["token_type"] == "bearer"

    async def test_admin_login(self, client):
        from app.utils.config import settings

        r = await client.post(
            "/api/auth/token",
            data={
                "username": settings.INITIAL_USER_NAME,
                "password": settings.INITIAL_USER_PASS,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code == 200, r.text
        token = r.json()
        assert "access_token" in token
        assert token["token_type"] == "bearer"
