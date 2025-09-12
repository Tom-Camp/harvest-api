# tests/test_routes.py
import pytest


@pytest.mark.asyncio
async def test_create_user(client):
    payload = {"email": "alice@example.com", "full_name": "Alice"}
    resp = await client.post("/users", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == payload["email"]
    assert "id" in data


@pytest.mark.asyncio
async def test_protected_endpoint_denied(client):
    resp = await client.get("/protected", params={"user_id": "bob"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_protected_endpoint_allowed(client):
    # Insert a policy for user “bob” – note the await!
    from app.casbin.casbin_config import casbin_manager

    await casbin_manager.add_policy("bob", "/protected", "read")

    resp = await client.get("/protected", params={"user_id": "bob"})
    assert resp.status_code == 200
    assert "authorized" in resp.json()["msg"]
