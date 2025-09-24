from typing import Dict, List

import pytest
from httpx import AsyncClient

from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestPageRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 403),
            ("", 401),
        ],
    )
    async def test_create_page(
        self,
        client: AsyncClient,
        default_user: Dict,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
        headers = await get_auth_headers(client=client, user_name=username)
        username = test_as.username if isinstance(test_as, User) else "Anonymous"
        payload = {
            "title": f"{username} Other Page",
            "body": "This is a test page",
        }
        response = await client.post(url="/api/pages/", json=payload, headers=headers)
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 200),
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_read_pages(
        self,
        default_pages: List,
        default_user: Dict,
        client: AsyncClient,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
        headers = await get_auth_headers(client=client, user_name=username)

        response = await client.get(url="/api/pages/", headers=headers)

        assert isinstance(response.json(), List)
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_read_my_pages(
        self,
        client: AsyncClient,
        default_user: Dict,
        default_pages: List,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
        headers = await get_auth_headers(client=client, user_name=username)

        response = await client.get(
            url="/api/pages/my",
            headers=headers,
        )

        assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_read_page(self, client: AsyncClient, default_pages: List):
        page_response = await client.get(url=f"/api/pages/{default_pages[0].id}")
        assert page_response.json().get("title") == default_pages[0].title

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
        default_user: Dict,
        default_pages: List,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
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
        default_user: dict,
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
        username = test_as.username if test_as else None
        headers = await get_auth_headers(client=client, user_name=username)
        delete_garden = await client.delete(
            url=f"/api/pages/{to_delete.get('id', '')}", headers=headers
        )
        assert delete_garden.status_code == expected_status
