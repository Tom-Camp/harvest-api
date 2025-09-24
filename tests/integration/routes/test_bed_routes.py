import pytest
from httpx import AsyncClient

from tests.helpers.test_helpers import get_auth_headers


class TestBedRoutes:

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
    async def test_create_bed(
        self,
        client: AsyncClient,
        default_user: dict,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
        headers = await get_auth_headers(client=client, user_name=username)

        garden_response = await client.get(url="/api/gardens/my", headers=headers)
        garden_id = (
            garden_response.json()[0].get("id")
            if garden_response.status_code == 200
            else None
        )

        response = await client.post(
            url="/api/beds",
            json={
                "name": "A note about my garden",
                "description": "This is the garden",
                "garden_id": garden_id,
            },
            headers=headers,
        )
        assert response.status_code == expected_status
