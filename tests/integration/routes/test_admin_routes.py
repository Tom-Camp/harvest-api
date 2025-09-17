from typing import Dict

import pytest


class TestAdminRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 403),
            ("authenticated", 403),
        ],
    )
    async def test_assign_role(
        self, client, default_user, user_name: str, expected_status: int
    ):
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        user_user = default_user.get("authenticated")
        response = await client.post(
            url="/api/admin/assign-role",
            json={
                "user_id": str(user_user.id),
                "username": user_user.username,
                "role_name": "moderator",
            },
            headers=headers,
        )
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 403),
            ("authenticated", 403),
        ],
    )
    async def test_remove_role(
        self, client, default_user, user_name: str, expected_status: int
    ):
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        user_user = default_user.get("authenticated")
        response = await client.post(
            url="/api/admin/remove-role",
            json={
                "user_id": str(user_user.id),
                "username": user_user.username,
                "role_name": "moderator",
            },
            headers=headers,
        )
        assert response.status_code == expected_status

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
    async def test_check_permissions(
        self, client, default_user, user_name: str, expected_status: int
    ):
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        user_user = default_user.get("authenticated")
        response = await client.post(
            url="/api/admin/check-permission",
            json={
                "user_id": str(user_user.id),
                "username": user_user.username,
                "resource": "policy",
                "action": "read",
            },
            headers=headers,
        )
        assert response.status_code == expected_status

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
    async def test_get_user_roles(
        self, client, default_user, user_name: str, expected_status: int
    ):
        headers: Dict[str, str] = {}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        moderator_user = default_user.get("moderator")
        response = await client.get(
            url=f"/api/admin/user-roles/{moderator_user.id}",
            headers=headers,
        )
        assert response.status_code == expected_status

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
    async def test_get_role_users(
        self, client, default_user, user_name: str, expected_status: int
    ):
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        response = await client.get(
            url="/api/admin/role-users/moderator",
            headers=headers,
        )
        assert response.status_code == expected_status

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
    async def test_debug_role_users(
        self, client, default_user, user_name: str, expected_status: int
    ):
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        response = await client.get(
            url="/api/admin/role-users/moderator",
            headers=headers,
        )
        assert response.status_code == expected_status
