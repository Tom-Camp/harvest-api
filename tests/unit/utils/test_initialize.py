import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.utils.initialize import setup_initial_admin


@pytest.mark.asyncio
async def test_setup_initial_admin_creates_user(monkeypatch):
    # Arrange: controlled settings
    monkeypatch.setenv("INITIAL_USER_NAME", "admin_test")
    monkeypatch.setenv("INITIAL_USER_MAIL", "admin@example.com")
    monkeypatch.setenv("INITIAL_USER_PASS", "secret123")
    # If settings is a Pydantic Settings object loaded at import time,
    # force a reload or patch attributes directly:
    # monkeypatch.setattr(settings, "INITIAL_USER_NAME", "admin_test", raising=False)
    # monkeypatch.setattr(settings, "INITIAL_USER_MAIL", "admin@example.com", raising=False)
    # monkeypatch.setattr(settings, "INITIAL_USER_PASS", "secret123", raising=False)

    fake_id = uuid.uuid4()

    async def _get_user_by_username(session, username):
        return None

    class DummyUser:
        def __init__(self, id_, username):
            self.id = id_
            self.username = username

    async def _create_user(session, user_create):
        return DummyUser(fake_id, user_create.username)

    # Patch async CRUDs and the log handler
    with (
        patch(
            "app.users.user_crud.UserCRUD.get_user_by_username",
            new=AsyncMock(side_effect=_get_user_by_username),
        ) as m_get,
        patch(
            "app.users.user_crud.UserCRUD.create_user",
            new=AsyncMock(side_effect=_create_user),
        ) as m_create,
        patch("app.logging.log_handler.log_handler.log_security_event") as m_log,
    ):
        # Provide a fake AsyncSession if needed
        session = object()
        result = await setup_initial_admin(session)

        # Assert: created and logged
        assert result == fake_id
        m_get.assert_awaited_once()
        m_create.assert_awaited_once()
        m_log.assert_called_once()


@pytest.mark.asyncio
async def test_setup_initial_admin_already_exists(monkeypatch, caplog):
    monkeypatch.setattr(
        "app.utils.config.settings",
        type(
            "S",
            (),
            {
                "INITIAL_USER_NAME": "admin_test",
                "INITIAL_USER_MAIL": "admin@example.com",
                "INITIAL_USER_PASS": "secret123",
                "INITIAL_USER_LOCATION": "Lebanon, Kansas",
            },
        )(),
        raising=False,
    )

    class DummyUser:
        def __init__(self, id_, username):
            self.id = id_
            self.username = username

    existing = DummyUser(uuid.uuid4(), "admin_test")

    with (
        patch(
            "app.users.user_crud.UserCRUD.get_user_by_username",
            new=AsyncMock(return_value=existing),
        ) as m_get,
        patch("app.users.user_crud.UserCRUD.create_user", new=AsyncMock()) as m_create,
        patch("app.logging.log_handler.StructlogHandler.log_security_event") as m_log,
    ):
        result = await setup_initial_admin(object())
        assert result == existing.id
        m_get.assert_awaited_once()
        m_create.assert_not_called()
        m_log.assert_not_called()
