import uuid

import pytest
from httpx import AsyncClient

from app.models.garden_models import Garden
from app.models.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestGardenNoteReadRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_read_garden_note(
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
            garden_id = garden.id
            response = await client.post(
                url="/api/garden-notes/",
                json={"note": "this is the first note", "garden_id": str(garden_id)},
                headers=headers,
            )
            new_note = response.json()
            assert response.status_code == 200
            if response.status_code == 200:
                get_response = await client.get(
                    url=f"/api/garden-notes/{new_note.get('id')}",
                    headers=headers,
                )
                assert get_response.status_code == expected_status
                note = response.json()
                assert note.get("note") == "this is the first note"
        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_read_garden_note_unauthenticated(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("test_user")
        if isinstance(garden, Garden):
            post_user = default_user.get("test_user")
            username = post_user.username if isinstance(post_user, User) else ""
            post_headers = await get_auth_headers(client=client, user_name=username)
            garden_id = garden.id if isinstance(garden, Garden) else garden.get("id")
            response = await client.post(
                url="/api/garden-notes/",
                json={"note": "this is the first note", "garden_id": str(garden_id)},
                headers=post_headers,
            )
            new_note = response.json()
            assert response.status_code == 200
            if response.status_code == 200:
                get_response = await client.get(
                    url=f"/api/garden-notes/{new_note.get('id')}",
                    headers=headers,
                )
                assert get_response.status_code == 401
                note = response.json()
                assert note.get("note") == "this is the first note"
        else:
            pytest.fail("No garden found for user test_user")

    @pytest.mark.asyncio
    async def test_read_garden_note_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(
            url=f"/api/garden-notes/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_read_garden_notes(
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
                url=f"/api/garden-notes/notes/{garden.id}",
                headers=headers,
            )
            assert response.status_code == expected_status
            assert isinstance(response.json(), list)

        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_read_garden_notes_unauthenticated(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("test_user")
        if isinstance(garden, Garden):
            garden_id = garden.id
            response = await client.get(
                url=f"/api/garden-notes/notes/{garden_id}",
                headers=headers,
            )
            assert response.status_code == 401
        else:
            pytest.fail("No garden found for user test_user")

    @pytest.mark.asyncio
    async def test_read_garden_notes_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(
            url=f"/api/garden-notes/notes/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404
