from typing import Dict

import pytest
from httpx import AsyncClient

from app.users.user_models import User


class TestAuthRoutes:

    @pytest.mark.asyncio
    async def test_register(self, client: AsyncClient):
        payload = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "milk prairie island desert",
        }
        response = await client.post(
            url="/api/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        payload: Dict[str, str] = {
            "username": "alice",
            "email": "alice@example",
            "password": "milk prairie island desert",
        }
        response = await client.post(
            url="/api/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_invalid_username(self, client: AsyncClient):
        payload: Dict[str, str] = {
            "email": "alice@example",
            "password": "milk prairie island desert",
        }
        response = await client.post(
            url="/api/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_password_length(self, client: AsyncClient):
        payload: Dict[str, str] = {
            "email": "alice@example",
            "password": "6j9ZI43/jcA",
        }
        response = await client.post(
            url="/api/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_password_complexity(self, client: AsyncClient):
        payload: Dict[str, str] = {
            "email": "alice@example",
            "password": "lemon meringue pie",
        }
        response = await client.post(
            url="/api/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_password_breach(self, client: AsyncClient):
        payload: Dict[str, str] = {
            "email": "alice@example",
            "password": "correct horse battery staple",
        }
        response = await client.post(
            url="/api/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_for_access_token(
        self, client: AsyncClient, default_user: Dict[str, User]
    ):
        user = default_user.get("admin")
        payload: Dict[str, str] = {
            "username": user.username,
            "password": "UkeV3BNUIL7x/n0J",
        }
        response = await client.post(
            url="/api/auth/token",
            data=payload,
        )
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_login_for_access_token_invalid_password(
        self, client: AsyncClient, default_user: Dict[str, User]
    ):
        user = default_user.get("admin")
        payload = {
            "username": user.username,
            "password": "YkeV3BNUIL7x/n0J",
        }
        response = await client.post(
            url="/api/auth/token",
            data=payload,
        )
        assert response.status_code == 401
        assert response.json().get("detail", "") == "Incorrect username or password"
