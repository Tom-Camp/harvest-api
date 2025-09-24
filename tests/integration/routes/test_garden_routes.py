import pytest
from httpx import AsyncClient

from tests.helpers.test_helpers import get_auth_headers


class TestGardenRoutes:

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
    async def test_create_garden(
        self,
        client: AsyncClient,
        default_user: dict,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
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
    async def test_read_gardens(
        self,
        client: AsyncClient,
        default_user: dict,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
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
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_read_user_gardens(
        self,
        client: AsyncClient,
        default_user: dict,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
        headers = await get_auth_headers(client=client, user_name=username)
        response = await client.get(
            url=f"/api/gardens/user/{test_as.id}",
            headers=headers,
        )
        assert response.status_code == expected_status

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
    async def test_read_garden_my(
        self,
        client: AsyncClient,
        default_user: dict,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
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
            ("", 200),
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_read_garden(
        self,
        client: AsyncClient,
        default_user: dict,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
        headers = await get_auth_headers(client=client, user_name=username)
        garden_list = await client.get(
            url="/api/gardens/",
            headers=headers,
        )
        gardens = garden_list.json()
        response = await client.get(
            url=f"/api/gardens/{gardens[0].get('id')}",
            headers=headers,
        )

        assert response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 403),
        ],
    )
    async def test_update_garden(
        self,
        client: AsyncClient,
        default_user: dict,
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
        headers = await get_auth_headers(client=client, user_name=username)
        garden_response = await client.get(url="/api/gardens/")
        update_garden = garden_response.json()
        response = await client.put(
            url=f"/api/gardens/{update_garden[0].get('id')}",
            json={
                "name": f"{user_name}'s new garden",
                "description": "This is Updated garden",
                "location": "Delta, Colorado",
                "is_private": True,
            },
            headers=headers,
        )
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_update_garden_own(
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
        update_garden = garden_response.json()
        response = await client.put(
            url=f"/api/gardens/{update_garden[0].get('id', '')}",
            json={
                "name": f"{user_name}'s new garden",
                "description": "This is Updated garden",
                "location": "Delta, Colorado",
                "is_private": True,
            },
            headers=headers,
        )
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 403),
        ],
    )
    async def test_delete_garden(
        self,
        client: AsyncClient,
        default_user: dict,
        user_name: str,
        expected_status: int,
    ):
        headers = await get_auth_headers(client=client, user_name="test_admin_user")
        new_garden = await client.post(
            url="/api/gardens/",
            json={
                "name": "Admin's new garden",
                "description": "This is a test garden",
                "location": "Delta, Colorado",
            },
            headers=headers,
        )
        to_delete = new_garden.json()

        test_as = default_user.get(user_name, "")
        username = test_as.username if test_as else None
        headers = await get_auth_headers(client=client, user_name=username)
        delete_garden = await client.delete(
            url=f"/api/gardens/{to_delete.get('id')}", headers=headers
        )
        assert delete_garden.status_code == expected_status
