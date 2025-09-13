import pytest


@pytest.mark.asyncio
async def test_register_creates_user(client):
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123",
    }
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
