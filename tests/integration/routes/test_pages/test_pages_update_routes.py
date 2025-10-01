import uuid

import pytest
from httpx import AsyncClient

from app.pages.page_models import Page
from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestPageUpdateRoutes:

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
    async def test_update_page(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_pages: list[Page],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if hasattr(test_as, "username") else None
        headers = await get_auth_headers(client=client, user_name=username)
        page = default_pages[-1]
        page_response = await client.get(url=f"/api/pages/{page.id}")
        to_update = page_response.json()

        username = test_as.username if isinstance(test_as, User) else "Anonymous"
        payload = {"title": f"Updated by {username}"}
        response = await client.put(
            url=f"/api/pages/{to_update.get('id')}", json=payload, headers=headers
        )
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_update_page_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.put(
            url=f"/api/pages/{bad_id}",
            json={"title": f"Updated by {username}"},
            headers=headers,
        )
        assert response.status_code == 404
