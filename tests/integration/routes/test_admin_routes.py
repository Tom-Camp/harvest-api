import pytest


class TestAdminRoutes:
    headers: dict = {"Content-Type": "application/json"}

    @pytest.mark.asyncio
    async def test_role_add(self, client, default_user):
        admin = default_user.get("admin")
        get_token = await client.post(
            "/api/auth/token",
            data={"username": admin.username, "password": "Passw0rd!123"},
        )
        self.headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        user_user = default_user.get("user")
        response = await client.post(
            "api/admin/assign-role",
            json={
                "user_id": str(user_user.id),
                "username": user_user.username,
                "role_name": "moderator",
            },
            headers=self.headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_role_remove(self, client, default_user):
        admin = default_user.get("admin")
        get_token = await client.post(
            "/api/auth/token",
            data={"username": admin.username, "password": "Passw0rd!123"},
        )
        self.headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        user_user = default_user.get("user")
        response = await client.post(
            "api/admin/remove-role",
            json={
                "user_id": str(user_user.id),
                "username": user_user.username,
                "role_name": "moderator",
            },
            headers=self.headers,
        )
        assert response.status_code == 200
