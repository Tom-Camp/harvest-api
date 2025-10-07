import pytest

from app.models.user_models import User


class TestAuthRoutes:

    @pytest.mark.asyncio
    async def test_register(self, client):
        response = await client.post(
            url="/api/auth/register",
            json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "milk prairie island desert",
            },
            headers={"Content-Type": "application/json"},
        )
        data = response.json()
        assert response.status_code == 200
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"

    @pytest.mark.asyncio
    async def test_register_username_taken(self, client, default_user: dict[str, User]):
        response = await client.post(
            url="/api/auth/register",
            json={
                "username": "test_user_user",
                "email": "testuser@example.com",
                "password": "milk prairie island desert",
            },
            headers={"Content-Type": "application/json"},
        )
        data = response.json()
        assert response.status_code == 400
        assert data.get("detail") == "Username already registered"

    @pytest.mark.asyncio
    async def test_register_email_taken(self, client, default_user: dict[str, User]):
        response = await client.post(
            url="/api/auth/register",
            json={
                "username": "not_test_user_user",
                "email": "test_user@example.com",
                "password": "milk prairie island desert",
            },
            headers={"Content-Type": "application/json"},
        )
        data = response.json()
        assert response.status_code == 400
        assert data.get("detail") == "Email already registered"

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        response = await client.post(
            url="/api/auth/register",
            json={
                "username": "alice",
                "email": "alice@example",
                "password": "milk prairie island desert",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_invalid_username(self, client):
        response = await client.post(
            url="/api/auth/register",
            json={
                "email": "alice@example.com",
                "password": "milk prairie island desert",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_password_length(self, client):
        response = await client.post(
            url="/api/auth/register",
            json={
                "email": "alice@example",
                "password": "6j9ZI43/jcA",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_password_complexity(self, client):
        response = await client.post(
            url="/api/auth/register",
            json={
                "email": "alice@example",
                "password": "lemon meringue pie",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_password_breach(self, client):
        response = await client.post(
            url="/api/auth/register",
            json={
                "email": "alice@example",
                "password": "correct horse battery staple",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_for_access_token(self, client, default_user: dict[str, User]):
        user = default_user.get("admin")
        if isinstance(user, User):
            response = await client.post(
                url="/api/auth/token",
                json={
                    "username": user.username,
                    "password": "UkeV3BNUIL7x/n0J",
                },
            )
            assert "access_token" in response.json()
        else:
            pytest.fail("No User found for user admin")

    @pytest.mark.asyncio
    async def test_login_for_access_token_invalid_password(
        self, client, default_user: dict[str, User]
    ):
        user = default_user.get("admin")
        if isinstance(user, User):
            response = await client.post(
                url="/api/auth/token",
                json={
                    "username": user.username,
                    "password": "YkeV3BNUIL7x/n0J",
                },
            )
            assert response.status_code == 401
            assert response.json().get("detail", "") == "Incorrect username or password"
        else:
            pytest.fail("No User found for user authenticated")
