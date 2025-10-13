import uuid

import pytest
from httpx import AsyncClient

from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestAdminRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("test_admin", 200),
            ("test_moderator", 403),
            ("test_authenticated", 403),
        ],
    )
    async def test_assign_role(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        user_user = default_user.get("test_user")
        if isinstance(user_user, User):
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
        else:
            pytest.fail("No User found for user authenticated")

    @pytest.mark.asyncio
    async def test_assign_role_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.post(
            url="/api/admin/assign-role",
            json={
                "user_id": str(bad_id),
                "username": "bad_id",
                "role_name": "moderator",
            },
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("test_admin", 200),
            ("test_moderator", 403),
            ("test_authenticated", 403),
        ],
    )
    async def test_remove_role(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        user_user = default_user.get("authenticated")
        if isinstance(user_user, User):
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
        else:
            pytest.fail("No User found for user authenticated")

    @pytest.mark.asyncio
    async def test_remove_role_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.post(
            url="/api/admin/remove-role",
            json={
                "user_id": str(bad_id),
                "username": "bad_id",
                "role_name": "moderator",
            },
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 403),
        ],
    )
    async def test_check_permissions(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else None
        headers = await get_auth_headers(client=client, user_name=username)
        user_user = default_user.get("test_user")
        if isinstance(user_user, User):
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
        else:
            pytest.fail("No User found for user authenticated")

    @pytest.mark.asyncio
    async def test_check_permissions_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.post(
            url="/api/admin/check-permission",
            json={
                "user_id": str(bad_id),
                "username": "bad_id",
                "resource": "policy",
                "action": "read",
            },
            headers=headers,
        )
        assert response.status_code == 404

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
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else None
        headers = await get_auth_headers(client=client, user_name=username)
        moderator_user = default_user.get("moderator")
        if isinstance(moderator_user, User):
            response = await client.get(
                url=f"/api/admin/user-roles/{moderator_user.id}",
                headers=headers,
            )
            assert response.status_code == expected_status
        else:
            pytest.fail("No User found for user moderator")

    @pytest.mark.asyncio
    async def test_get_user_roles_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(
            url=f"/api/admin/user-roles/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 403),
        ],
    )
    async def test_get_role_users(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else None
        headers = await get_auth_headers(client=client, user_name=username)
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
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 403),
        ],
    )
    async def test_debug_role_users(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else None
        headers = await get_auth_headers(client=client, user_name=username)
        response = await client.get(
            url="/api/admin/role-users/moderator",
            headers=headers,
        )
        assert response.status_code == expected_status
