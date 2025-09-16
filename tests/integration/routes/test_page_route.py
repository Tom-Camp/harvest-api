from typing import List

import pytest


class TestPageRoutes:
    headers: dict = {"Content-Type": "application/json"}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_user,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("user", 403),
            ("", 403),
        ],
    )
    async def test_create_page(
        self, client, default_user, test_user: str, expected_status: int
    ):
        test_as = default_user.get(test_user)
        if test_user:
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            self.headers["Authorization"] = (
                f"Bearer {get_token.json().get('access_token')}"
            )
        payload = {
            "title": f"{test_as.username} Test Page",
            "body": "This is a test page",
        }
        create_page_response = await client.post(
            url="/api/pages/", json=payload, headers=self.headers
        )
        assert create_page_response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_user,expected_status",
        [
            ("", 200),
            ("admin", 200),
            ("moderator", 200),
            ("user", 200),
        ],
    )
    async def test_read_pages(
        self, default_pages, default_user, client, test_user: str, expected_status: int
    ):
        test_as = default_user.get(test_user)
        if test_as:
            get_token = await client.post(
                url="/api/auth/token",
                data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
            )
            self.headers["Authorization"] = (
                f"Bearer {get_token.json().get('access_token')}"
            )

        read_page_response = await client.get(url="/api/pages/", headers=self.headers)

        assert isinstance(read_page_response.json(), List)

    @pytest.mark.asyncio
    async def test_read_my_pages(self, client, default_user, default_pages):
        test_as = default_user.get("moderator")
        get_token = await client.post(
            url="/api/auth/token",
            data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
        )
        self.headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"

        my_pages_response = await client.get(
            url="/api/pages/my",
            headers=self.headers,
        )

        page_list = my_pages_response.json()
        assert isinstance(page_list, List)
        assert page_list[2].get("title") == "Page three"

    @pytest.mark.asyncio
    async def test_read_page(self, client, default_pages):
        page_response = await client.get(url=f"/api/pages/{default_pages[0].id}")
        assert page_response.json().get("title") == "Page one"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_user,expected_status",
        [
            ("", 200),
            ("admin", 200),
            ("moderator", 200),
            ("user", 200),
        ],
    )
    async def test_update_page(
        self, client, default_user, default_pages, test_user, expected_status
    ):
        page = default_pages[0]
        page_response = await client.get(url=f"/api/pages/{page.id}")
        page_id = page_response.json()
        test_as = default_user.get(test_user)
        if test_as:
            get_token = await client.post(
                url="/api/auth/token",
                data={
                    "username": test_as.username,
                    "password": "UkeV3BNUIL7x/n0J",
                },
            )
            self.headers["Authorization"] = (
                f"Bearer {get_token.json().get('access_token')}"
            )

        payload = {"title": f"Updated by {test_user}"}
        update_response = await client.put(
            url=f"/api/pages/{page_id.get('id')}", json=payload, headers=self.headers
        )
        assert update_response.status_code == expected_status
        if update_response.status_code == 200:
            assert update_response.json().title == f"/api/pages/{test_user}"
