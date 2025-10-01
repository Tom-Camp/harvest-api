import pytest
from httpx import AsyncClient

from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestPageCreateRoutes:

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
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if hasattr(test_as, "username") else ""
        headers = await get_auth_headers(client=client, user_name=username)
        username = test_as.username if isinstance(test_as, User) else "Anonymous"
        payload = {
            "title": f"{username} Other Page",
            "body": "This is a test page",
        }
        response = await client.post(url="/api/pages/", json=payload, headers=headers)
        assert response.status_code == expected_status
