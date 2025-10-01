import uuid

import pytest
from httpx import AsyncClient

from app.gardens.garden_models import Garden
from app.users.user_models import User
from tests.helpers.test_helpers import get_auth_headers


class TestBedNoteDeleteRoutes:

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
    async def test_delete_bed_note(
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
        garden = default_gardens.get("tester")
        if isinstance(garden, Garden):
            bed_id = garden.beds[0].id
            create_response = await client.post(
                url="/api/bed-notes/",
                json={"note": "My new bed note", "bed_id": str(bed_id)},
                headers=create_headers,
            )
            note = create_response.json()

            test_as = default_user.get(user_name, "")
            username = test_as.username if isinstance(test_as, User) else ""
            headers = await get_auth_headers(client=client, user_name=username)

            delete_note = await client.delete(
                url=f"/api/bed-notes/{note.get('id')}", headers=headers
            )
            assert delete_note.status_code == expected_status

        else:
            pytest.fail("No garden found for user tester")

    @pytest.mark.asyncio
    async def test_delete_bed_note_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.delete(url=f"/api/bed-notes/{bad_id}", headers=headers)
        assert response.status_code == 404
