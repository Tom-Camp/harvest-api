import uuid

import pytest
from httpx import AsyncClient

from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import create_note, get_auth_headers


class TestBedNoteReadRoutes:
    note_json: dict = {"note": "this is a bed note", "bed_id": ""}
    note_url: str = "/api/bed-notes/"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("admin", 200),
            ("moderator", 200),
            ("authenticated", 200),
        ],
    )
    async def test_read_bed_note(
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
            self.note_json["bed_id"] = str(garden.beds[0].id)
            new_note = await create_note(
                client=client,
                note=self.note_json,
                url=self.note_url,
                headers=headers,
            )
            response = await client.get(
                url=f"/api/bed-notes/{new_note.get('id')}",
                headers=headers,
            )
            assert response.status_code == expected_status
            note = response.json()
            assert note.get("note") == "this is a bed note"
        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_read_bed_note_unauthenticated(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("authenticated")
        if isinstance(garden, Garden):
            post_user = default_user.get("authenticated")
            username = post_user.username if isinstance(post_user, User) else ""
            post_headers = await get_auth_headers(client=client, user_name=username)
            self.note_json["bed_id"] = str(garden.beds[0].id)
            new_note = await create_note(
                client=client,
                note=self.note_json,
                url=self.note_url,
                headers=post_headers,
            )
            response = await client.get(
                url=f"/api/bed-notes/{new_note.get('id')}",
                headers=headers,
            )
            assert response.status_code == 401
        else:
            pytest.fail("No garden found for user tester")

    @pytest.mark.asyncio
    async def test_read_bed_note_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(
            url=f"/api/bed-notes/{bad_id}",
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
    async def test_read_bed_notes(
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
            response = await client.get(
                url=f"/api/bed-notes/notes/{bed_id}",
                headers=headers,
            )
            assert response.status_code == expected_status
            assert isinstance(response.json(), list)

        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_read_bed_notes_unauthenticated(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("authenticated")
        if isinstance(garden, Garden):
            bed_id = garden.beds[0].id
            response = await client.get(
                url=f"/api/bed-notes/notes/{bed_id}",
                headers=headers,
            )
            assert response.status_code == 401
        else:
            pytest.fail("No garden found for user tester")

    @pytest.mark.asyncio
    async def test_read_bed_notes_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.get(
            url=f"/api/bed-notes/notes/{bad_id}",
            headers=headers,
        )
        assert response.status_code == 404
