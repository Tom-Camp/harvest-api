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
        ],
    )
    async def test_create_page(
        self, client, default_user, test_user: str, expected_status: int
    ):
        test_as = default_user.get(test_user)
        get_token = await client.post(
            url="/api/auth/token",
            data={"username": test_as.username, "password": "UkeV3BNUIL7x/n0J"},
        )
        self.headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
        payload = {
            "title": f"{test_as.username} Test Page",
            "body": "This is a test page",
        }
        create_page_response = await client.post(
            url="/api/pages/", json=payload, headers=self.headers
        )
        assert create_page_response.status_code == expected_status
