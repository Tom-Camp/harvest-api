from typing import List

import pytest

from app.users.user_models import User


class TestPageRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
            ("", 401),
        ],
    )
    async def test_create_page(
        self, client, default_user, user_name: str, expected_status: int
    ):
        headers: dict = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
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
        self, default_pages, default_user, client, user_name: str, expected_status: int
    ):
        headers: dict = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"

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
        self, client, default_user, default_pages, user_name: str, expected_status: int
    ):
        headers: dict = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"

        response = await client.get(
            url="/api/pages/my",
            headers=headers,
        )

        assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_read_page(self, client, default_pages):
        page_response = await client.get(url=f"/api/pages/{default_pages[0].id}")
        assert page_response.json().get("title") == default_pages[0].title

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
    async def test_update_page(
        self, client, default_user, default_pages, user_name, expected_status
    ):
        headers: dict = {"Content-Type": "application/json"}
        if test_as := default_user.get(user_name, ""):
            get_token = await client.post(
                url="/api/auth/token",
                data={
                    "username": test_as.username,
                    "password": "UkeV3BNUIL7x/n0J",
                },
            )
            headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        page = default_pages[-1]
        page_response = await client.get(url=f"/api/pages/{page.id}")
        to_update = page_response.json()

        username = test_as.username if isinstance(test_as, User) else "Anonymous"
        payload = {"title": f"Updated by {username}"}
        response = await client.put(
            url=f"/api/pages/{to_update.get('id')}", json=payload, headers=headers
        )
        assert response.status_code == expected_status
