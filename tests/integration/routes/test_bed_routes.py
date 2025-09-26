import pytest
from httpx import AsyncClient

from app.gardens.garden_models import Garden
from app.users.user_models import User
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
    async def test_read_beds(
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
        garden = default_gardens.get("authenticated")
        if isinstance(garden, Garden):
            response = await client.get(url=f"/api/beds/{garden.id}", headers=headers)
            assert response.status_code == expected_status
            assert isinstance(response.json(), list)
        else:
            pytest.fail("No garden found for user authenticated")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_read_bed(
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

        garden = default_gardens.get("tester", "")
        if isinstance(garden, Garden):
            bed = garden.beds[0]
            response = await client.get(
                url=f"/api/beds/{garden.id}/{bed.id}", headers=headers
            )

            assert response.status_code == expected_status
        else:
            pytest.fail("No garden found for user tester")
