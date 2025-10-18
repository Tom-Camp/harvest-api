import pytest
from httpx import AsyncClient

from app.models.garden_models import Garden
from app.models.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestBedCreateRoutes:

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
    async def test_create_bed(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)

        garden = default_gardens.get(user_name)
        garden_id = garden.id if isinstance(garden, Garden) else ""
        response = await client.post(
            url="/api/beds",
            json={
                "name": f"The main bed for {username}",
                "description": "This is the garden",
                "garden_id": str(garden_id),
            },
            headers=headers,
        )
        new_bed = response.json()
        assert response.status_code == expected_status
        if response.status_code == 200:
            assert new_bed.get("name") == f"The main bed for {username}"
