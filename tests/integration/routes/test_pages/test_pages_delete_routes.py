import uuid

import pytest
from httpx import AsyncClient

from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestPageDeleteRoutes:

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
    async def test_delete_page(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        headers = await get_auth_headers(client=client, user_name="test_admin_user")
        new_page = await client.post(
            url="/api/pages/",
            json={
                "title": "Admin's new page",
                "body": "This is a test page",
            },
            headers=headers,
        )
        to_delete = new_page.json()

        test_as = default_user.get(user_name, "")
        username = test_as.username if hasattr(test_as, "username") else None
        headers = await get_auth_headers(client=client, user_name=username)
        delete_page = await client.delete(
            url=f"/api/pages/{to_delete.get('id', '')}", headers=headers
        )
        assert delete_page.status_code == expected_status

    @pytest.mark.asyncio
    async def test_delete_page_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.delete(url=f"/api/pages/{bad_id}", headers=headers)
        assert response.status_code == 404
