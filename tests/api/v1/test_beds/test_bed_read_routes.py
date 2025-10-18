import uuid

import pytest
from httpx import AsyncClient

from app.models.garden_models import Garden
from app.models.user_models import User
from tests.helpers.test_helpers import create_bed, get_auth_headers


class TestBedReadRoutes:

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
    async def test_read_beds_own(
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
        garden = default_gardens.get("test_authenticated")
        if isinstance(garden, Garden):
            response = await client.get(
                url=f"/api/beds/garden/{garden.id}", headers=headers
            )
            assert response.status_code == expected_status
            if expected_status == 200:
                assert isinstance(response.json(), list)
        else:
            pytest.fail("No garden found for user authenticated")

    @pytest.mark.asyncio
    async def test_read_beds_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(url=f"/api/beds/garden/{bad_id}", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 403),
        ],
    )
    async def test_read_bed_any(
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

        garden = default_gardens.get("test_user", "")
        if isinstance(garden, Garden):
            new_bed = await create_bed(
                client=client, garden_id=str(garden.id), headers=headers
            )
            response = await client.get(
                url=f"/api/beds/{new_bed.get('id', '')}", headers=headers
            )

            assert response.status_code == expected_status
        else:
            pytest.fail("No garden found for user test_user")

    @pytest.mark.asyncio
    async def test_read_bed_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()

        response = await client.get(url=f"/api/beds/{bad_id}", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_read_bed_unauthenticated(
        self,
        client: AsyncClient,
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")

        garden = default_gardens.get("test_user", "")
        test_headers = await get_auth_headers(client=client, user_name="test_user")
        if isinstance(garden, Garden):
            new_bed = await create_bed(
                client=client, garden_id=str(garden.id), headers=test_headers
            )
            response = await client.get(
                url=f"/api/beds/{new_bed.get('id', '')}", headers=headers
            )

            assert response.status_code == 401
        else:
            pytest.fail("No garden found for user test_user")
