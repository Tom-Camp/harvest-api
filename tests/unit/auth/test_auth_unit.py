
from fastapi import HTTPException
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

import pytest
from jwt import decode, encode, InvalidSignatureError, InvalidTokenError

from app.auth import auth as auth_mod
from app.utils.config import settings


class DummyResult:

    def __init__(self, user):
        self._user = user

    def scalars(self):
        return SimpleNamespace(first=lambda: self._user)

    def first(self):
        return self._user


class FakeAsyncSession:
    def __init__(self, user):
        self._user = user

    async def execute(self, _statement):
        return DummyResult(self._user)


class DummyUser:

    def __init__(self, username, hashed_password, is_active: bool = True):
        self.username = username
        self.hashed_password = hashed_password
        self.is_active = is_active


class User:

    def __init__(self, is_active):
        self.is_active = is_active


def fake_decode(token, key, algorithms):
    return {"foo": "bar"}


class TestAuth:

    @pytest.mark.asyncio
    async def test_authenticate_user(self, default_user):
        test_user = default_user.get("moderator")
        session = FakeAsyncSession(test_user)
        user = await auth_mod.authenticate_user(session=session, username=test_user.username, password="UkeV3BNUIL7x/n0J")
        assert user.username == test_user.username

    @pytest.mark.asyncio
    async def test_authenticate_user_no_user(self):
        session = FakeAsyncSession(None)
        result = await auth_mod.authenticate_user(session=session, username="nonexistent", password="any-password")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self):
        hashed = auth_mod.get_password_hash("correct-password")
        user = DummyUser("alice", hashed_password=hashed)
        session = FakeAsyncSession(user)
        result = await auth_mod.authenticate_user(session, "alice", "wrong-password")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_access_token(self):
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await auth_mod.create_access_token(
            data={"sub": "test_user", "exp": 10},
            expires_delta=access_token_expires,
        )
        assert isinstance(access_token, str)
        assert len(access_token) > 0

    @pytest.mark.asyncio
    async def test_create_access_token_no_expire(self):
        access_token = await auth_mod.create_access_token(data={"sub": "test_user", "exp": 10})
        assert isinstance(access_token, str)
        assert len(access_token) > 0

    @pytest.mark.asyncio
    async def test_access_token_roundtrip_decode_matches_payload(self):
        payload = {
            "sub": "some_username",
            "exp": datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15),
        }
        token = encode(payload, settings.SECRET_KEY, algorithm=settings.HASH_ALGORITHM)
        decoded = decode(token, settings.SECRET_KEY, algorithms=[settings.HASH_ALGORITHM])
        assert decoded["sub"] == "some_username"

    @pytest.mark.asyncio
    async def test_access_token_verification_fails_with_wrong_key(self):
        token = encode({"sub": "123"}, settings.SECRET_KEY, algorithm=settings.HASH_ALGORITHM)
        with pytest.raises(InvalidSignatureError):
            decode(token, "wrong-secret", algorithms=[settings.HASH_ALGORITHM])

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_raises_401(self, monkeypatch):
        monkeypatch.setattr(auth_mod, "decode", fake_decode)
        session = FakeAsyncSession(user=None)

        with pytest.raises(HTTPException) as exc:
            await auth_mod.get_current_user(token="badtoken", session=session)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_missing_sub_raises_401(self, monkeypatch):
        monkeypatch.setattr(auth_mod, "decode", fake_decode)
        session = FakeAsyncSession(user=None)

        with pytest.raises(HTTPException) as exc:
            await auth_mod.get_current_user(token="tok", session=session)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_active_user(self):
        user = User(is_active=True)
        result = await auth_mod.get_current_active_user(current_user=user)
        assert result is user

    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive_raises_400(self):
        user = User(is_active=False)
        with pytest.raises(HTTPException) as exc:
            await auth_mod.get_current_active_user(current_user=user)
        assert exc.value.status_code == 400
        assert exc.value.detail == "Inactive user"
