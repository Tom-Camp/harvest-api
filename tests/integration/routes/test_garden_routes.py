import uuid

import pytest
from httpx import AsyncClient

from app.gardens.garden_models import Garden
from app.users.user_models import User
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
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
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
        test_id = test_as.id if hasattr(test_as, "id") else None
        response = await client.get(
            url=f"/api/gardens/user/{test_id}",
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
        test_as = default_user.get("admin", "")
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
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_read_garden_my(
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
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
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
        garden = default_gardens.get("tester_user")
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
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(
            url=f"/api/gardens/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 403),
            ("authenticated", 403),
        ],
    )
    async def test_update_garden(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):

        garden = default_gardens.get("tester")
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        if isinstance(garden, Garden):
            response = await client.put(
                url=f"/api/gardens/{garden.id}",
                json={
                    "name": f"{username}'s updated garden",
                    "description": "This has been Updated",
                },
                headers=headers,
            )
            assert response.status_code == expected_status
            if response.status_code == 200:
                assert response.json()["name"] == f"{username}'s updated garden"
        else:
            pytest.fail("No garden found for user tester")

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
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        update_garden = default_gardens.get(user_name, "")
        if isinstance(update_garden, Garden):
            response = await client.put(
                url=f"/api/gardens/{update_garden.id}",
                json={
                    "name": f"{user_name}'s updated garden",
                    "description": "This has been Updated",
                },
                headers=headers,
            )
            assert response.status_code == expected_status
            assert response.json()["name"] == f"{user_name}'s updated garden"
        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_update_garden_unauthenticated(
        self,
        client: AsyncClient,
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("tester_user")
        if isinstance(garden, Garden):
            response = await client.put(
                url=f"/api/gardens/{garden.id}",
                json={
                    "name": "Unauthenticated's updated garden",
                    "description": "This has been Updated",
                },
                headers=headers,
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_garden_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.put(
            url=f"/api/gardens/{bad_id}",
            json={
                "name": "Bad ID's updated garden",
                "description": "This has been Updated",
            },
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("admin", 200),
            ("moderator", 403),
            ("authenticated", 403),
        ],
    )
    async def test_delete_garden(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        create_as = default_user.get("tester", "")
        username = create_as.username if isinstance(create_as, User) else ""
        create_headers = await get_auth_headers(client=client, user_name=username)
        create_response = await client.post(
            url="/api/gardens/",
            json={
                "name": "My new garden",
                "description": "This is the garden",
                "location": "Delta, Colorado",
            },
            headers=create_headers,
        )
        garden_id = create_response.json()

        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        delete_garden = await client.delete(
            url=f"/api/gardens/{garden_id.get('id')}", headers=headers
        )
        assert delete_garden.status_code == expected_status

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_delete_garden_own(
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
            delete_garden = await client.delete(
                url=f"/api/gardens/{garden.id}", headers=headers
            )
            assert delete_garden.status_code == expected_status
        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_delete_garden_unauthenticated(
        self,
        client: AsyncClient,
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("tester_user")
        if isinstance(garden, Garden):
            response = await client.delete(
                url=f"/api/gardens/{garden.id}",
                headers=headers,
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_garden_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.delete(
            url=f"/api/gardens/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404
