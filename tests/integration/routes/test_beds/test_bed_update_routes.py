import uuid

import pytest
from httpx import AsyncClient

from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestBedUpdateRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 403),
            ("authenticated", 403),
        ],
    )
    async def test_update_bed(
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
        garden = default_gardens.get("tester")
        if isinstance(garden, Garden):
            bed_id = garden.beds[0].id
            response = await client.put(
                url=f"/api/beds/{bed_id}",
                json={
                    "name": f"Updated by {username}",
                },
                headers=headers,
            )
            assert response.status_code == expected_status
            if response.status_code == 200:
                data = response.json()
                assert data.get("name") == f"Updated by {username}"
        else:
            pytest.fail("No garden found for user admin")

    @pytest.mark.asyncio
    async def test_update_bed_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.put(
            url=f"/api/beds/{bad_id}",
            json={
                "name": f"Updated by {username}",
            },
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_update_bed_own(
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
        if isinstance(garden, Garden):
            bed_id = garden.beds[0].id
            response = await client.put(
                url=f"/api/beds/{bed_id}",
                json={
                    "name": f"Updated by {username}",
                },
                headers=headers,
            )
            assert response.status_code == expected_status
            if response.status_code == 200:
                data = response.json()
                assert data.get("name") == f"Updated by {username}"
        else:
            pytest.fail(f"No garden found for user {username}")

    @pytest.mark.asyncio
    async def test_update_bed_unauthenticated(
        self,
        client: AsyncClient,
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("authenticated")
        if isinstance(garden, Garden):
            bed_id = garden.beds[0].id
            response = await client.put(
                url=f"/api/beds/{bed_id}",
                json={
                    "name": "Updated by Unauthenticated",
                },
                headers=headers,
            )
            assert response.status_code == 401
        else:
            pytest.fail("No garden found for user authenticated")
