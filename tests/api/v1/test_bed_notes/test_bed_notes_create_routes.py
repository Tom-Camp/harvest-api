import uuid

import pytest
from httpx import AsyncClient

from app.models.garden_models import Garden
from app.models.user_models import User
from tests.helpers.test_helpers import create_bed, get_auth_headers


class TestBedNoteCreateRoutes:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_name,expected_status",
        [
            ("test_admin", 200),
            ("test_moderator", 200),
            ("test_authenticated", 200),
        ],
    )
    async def test_create_bed_note(
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
            new_bed = await create_bed(
                client=client, garden_id=str(garden.id), headers=headers
            )
            response = await client.post(
                url="/api/bed-notes/",
                json={"note": "this is a bed note", "bed_id": new_bed.get("id", "")},
                headers=headers,
            )
            data = response.json()
            assert response.status_code == expected_status
            assert data.get("note") == "this is a bed note"
        else:
            pytest.fail(f"No garden found for user {user_name}")

    @pytest.mark.asyncio
    async def test_create_bed_note_unauthenticated(
        self,
        client: AsyncClient,
        default_gardens: dict[str, Garden],
    ):
        headers = await get_auth_headers(client=client, user_name="")
        garden = default_gardens.get("test_user")
        post_header = await get_auth_headers(client=client, user_name="test_user")
        if isinstance(garden, Garden):
            new_bed = await create_bed(
                client=client, garden_id=str(garden.id), headers=post_header
            )
            response = await client.post(
                url="/api/bed-notes/",
                json={"note": "this is a bed note", "bed_id": new_bed.get("id", "")},
                headers=headers,
            )
            assert response.status_code == 401
        else:
            pytest.fail("No garden found for user test_user")

    @pytest.mark.asyncio
    async def test_create_bed_note_bad_id(
        self,
        client: AsyncClient,
        default_user: dict[str, User],
    ):
        test_as = default_user.get("test_admin", "")
        username = test_as.username if isinstance(test_as, User) else ""
        headers = await get_auth_headers(client=client, user_name=username)
        bad_id = uuid.uuid4()
        response = await client.post(
            url="/api/bed-notes/",
            json={"note": "this is the first note", "bed_id": str(bad_id)},
            headers=headers,
        )
        assert response.status_code == 404
