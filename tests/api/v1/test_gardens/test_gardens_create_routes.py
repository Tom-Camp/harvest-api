import pytest
from httpx import AsyncClient

from app.models.garden_models import Garden
from app.models.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestGardenCreateRoutes:

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
    async def test_create_garden(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        response = await client.post(
            url="/api/gardens/",
            json={
                "name": "My new garden",
                "description": "This is the garden",
                "location": "Delta, Colorado",
            },
            headers=headers,
        )
        assert response.status_code == expected_status
        assert isinstance(Garden(**response.json()), Garden)
