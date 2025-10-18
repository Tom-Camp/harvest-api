import uuid

import pytest
from httpx import AsyncClient

from app.models.garden_models import Garden
from app.models.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestGardenReadRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 200),
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_read_gardens(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        response = await client.get(
            url="/api/gardens/",
            headers=headers,
        )
        assert response.status_code == expected_status
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_read_user_gardens(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        get_user = default_user.get("test_authenticated", "")
        get_id = get_user.id if hasattr(get_user, "id") else None
        response = await client.get(
            url=f"/api/gardens/user/{get_id}",
            headers=headers,
        )
        assert response.status_code == expected_status
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_read_user_gardens_unauthenticated(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        test_id = ""
        response = await client.get(
            url=f"/api/gardens/user/{test_id}",
            headers=headers,
        )
        assert response.status_code == 307

    @pytest.mark.asyncio
    async def test_read_user_gardens_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(
            url=f"/api/gardens/user/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404

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
    async def test_read_garden_my(
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
        response = await client.get(
            url="/api/gardens/my",
            headers=headers,
        )
        assert response.status_code == expected_status
        if response.status_code == 200:
            assert isinstance(response.json(), list)
            assert response.json()[0].get("name") == "Default garden"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_read_garden(
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
            response = await client.get(
                url=f"/api/gardens/{garden.id}",
                headers=headers,
            )
            assert response.status_code == expected_status
            assert isinstance(response.json()["beds"], list)
        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_read_garden_unauthenticated(
        self,
        client: AsyncClient,
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("test_user")
        if isinstance(garden, Garden):
            response = await client.get(
                url=f"/api/gardens/{garden.id}",
                headers=headers,
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_read_garden_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(
            url=f"/api/gardens/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404
