import pytest


class TestAdminRoutes:
    headers: dict = {"Content-Type": "application/json"}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_user,expected_status",
        [
            ("admin", 200),
            ("moderator", 403),
            ("user", 403),
        ],
    )
    async def test_assign_role(
        self, client, default_user, test_user: str, expected_status: int
    ):
        test_as = default_user.get(test_user)
        get_token = await client.post(
            "/api/auth/token",
            data={"username": test_as.username, "password": "Passw0rd!123"},
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
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 403),
            ("user", 403),
        ],
    )
    async def test_role_remove(self, client, default_user, user_name, expected_status):
        test_as = default_user.get(user_name)
        get_token = await client.post(
            "/api/auth/token",
            data={"username": test_as.username, "password": "Passw0rd!123"},
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
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("user", 403),
        ],
    )
    async def test_check_permissions(
        self, client, default_user, user_name, expected_status
    ):
        test_as = default_user.get(user_name)
        get_token = await client.post(
            "/api/auth/token",
            data={"username": test_as.username, "password": "Passw0rd!123"},
        )
        self.headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        moderator_user = default_user.get("moderator")
        response = await client.post(
            "api/admin/check-permission",
            json={
                "user_id": str(moderator_user.id),
                "username": moderator_user.username,
                "resource": "roles",
                "action": "read",
            },
            headers=self.headers,
        )
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("user", 403),
        ],
    )
    async def test_get_user_roles(
        self, client, default_user, user_name, expected_status
    ):
        test_as = default_user.get(user_name)
        get_token = await client.post(
            "/api/auth/token",
            data={"username": test_as.username, "password": "Passw0rd!123"},
        )
        self.headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        moderator_user = default_user.get("moderator")
        response = await client.get(
            f"api/admin/user-roles/{moderator_user.id}",
            headers=self.headers,
        )
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("user", 403),
        ],
    )
    async def test_get_role_users(
        self, client, default_user, user_name, expected_status
    ):
        test_as = default_user.get(user_name)
        get_token = await client.post(
            "/api/auth/token",
            data={"username": test_as.username, "password": "Passw0rd!123"},
        )
        self.headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        response = await client.get(
            "api/admin/role-users/moderator",
            headers=self.headers,
        )
        assert response.status_code == expected_status
