import uuid

import pytest
from httpx import AsyncClient

from app.models.page_models import Page
from app.models.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestPageReadRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 200),
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_read_pages(
        self,
        default_pages: list[Page],
        default_user: dict[str, User],
        client: AsyncClient,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if hasattr(test_as, "username") else None
        headers = await get_auth_headers(client=client, user_name=username)

        response = await client.get(url="/api/pages/", headers=headers)

        assert isinstance(response.json(), list)
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_read_my_pages(
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

        response = await client.get(
            url="/api/pages/my",
            headers=headers,
        )

        assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_read_page(self, client: AsyncClient, default_pages: list[Page]):
        page_response = await client.get(url=f"/api/pages/{default_pages[0].id}")
        assert page_response.json().get("title") == default_pages[0].title

    @pytest.mark.asyncio
    async def test_read_page_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        bad_id = uuid.uuid4()
        response = await client.get(url=f"/api/pages/{bad_id}")
        assert response.status_code == 404
