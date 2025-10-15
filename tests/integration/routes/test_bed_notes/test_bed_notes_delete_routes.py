import uuid

import pytest
from httpx import AsyncClient

from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import create_note, get_auth_headers


class TestBedNoteDeleteRoutes:
    note_json: dict = {"note": "this is a bed note", "bed_id": ""}
    note_url: str = "/api/bed-notes/"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("", 401),
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 403),
        ],
    )
    async def test_delete_bed_note_any(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        create_as = default_user.get("test_user", "")
        username = create_as.username if isinstance(create_as, User) else ""
        create_headers = await get_auth_headers(client=client, user_name=username)
        garden = default_gardens.get("test_user")
        if isinstance(garden, Garden):
            self.note_json["bed_id"] = str(garden.beds[0].id)
            note = await create_note(
                client=client,
                note=self.note_json,
                url=self.note_url,
                headers=create_headers,
            )

            test_as = default_user.get(user_name, "")
            username = test_as.username if isinstance(test_as, User) else ""
            headers = await get_auth_headers(client=client, user_name=username)

            delete_note = await client.delete(
                url=f"/api/bed-notes/{note.get('id')}", headers=headers
            )
            assert delete_note.status_code == expected_status

        else:
            pytest.fail("No garden found for user test_user")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_delete_bed_note_own(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
        default_gardens: dict[str, Garden],
        user_name: str,
        expected_status: int,
    ):
        create_as = default_user.get(user_name, "")
        username = create_as.username if isinstance(create_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        garden = default_gardens.get(user_name)
        if isinstance(garden, Garden):
            self.note_json["bed_id"] = str(garden.beds[0].id)
            note = await create_note(
                client=client,
                note=self.note_json,
                url=self.note_url,
                headers=headers,
            )

            delete_note = await client.delete(
                url=f"/api/bed-notes/{note.get('id')}", headers=headers
            )
            assert delete_note.status_code == expected_status

        else:
            pytest.fail("No garden found for user test_user")

    @pytest.mark.asyncio
    async def test_delete_bed_note_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.delete(url=f"/api/bed-notes/{bad_id}", headers=headers)
        assert response.status_code == 404
