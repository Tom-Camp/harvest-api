import uuid

import pytest
from httpx import AsyncClient

from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestGardenNoteUpdateRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 403),
            ("authenticated", 403),
        ],
    )
    async def test_update_garden_notes(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        garden = default_gardens.get("tester")
        test_user_header = await get_auth_headers(
            client=client, user_name="test_user_user"
        )

        test_as = default_user.get(user_name, "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        if isinstance(garden, Garden):
            response = await client.post(
                url="/api/garden-notes/",
                json={"note": "this is the first note", "garden_id": str(garden.id)},
                headers=test_user_header,
            )
            note = response.json()
            response = await client.put(
                url=f"/api/garden-notes/{note.get('id')}",
                json={
                    "note": f"Updated by {username}",
                },
                headers=headers,
            )
            assert response.status_code == expected_status
            if response.status_code == 200:
                data = response.json()
                assert data.get("note") == f"Updated by {username}"

        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_update_garden_notes_unauthenticated(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
    ):
        garden = default_gardens.get("tester")
        test_user_header = await get_auth_headers(
            client=client, user_name="test_user_user"
        )

        headers = await get_auth_headers(client=client, user_name="")
        if isinstance(garden, Garden):
            response = await client.post(
                url="/api/garden-notes/",
                json={"note": "this is the first note", "garden_id": str(garden.id)},
                headers=test_user_header,
            )
            note = response.json()
            response = await client.put(
                url=f"/api/garden-notes/{note.get('id')}",
                json={
                    "note": "Updated by unauthenticated",
                },
                headers=headers,
            )
            assert response.status_code == 401

        else:
            pytest.fail("No garden found for user tester")

    @pytest.mark.asyncio
    async def test_update_garden_note_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.put(
            url=f"/api/garden-notes/{bad_id}",
            json={
                "note": f"Updated by {username}",
            },
            headers=headers,
        )
        assert response.status_code == 404
