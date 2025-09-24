from typing import Dict

from httpx import AsyncClient


async def get_auth_headers(
    client: AsyncClient, user_name: str | None
) -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if user_name:
        get_token = await client.post(
            url="/api/auth/token",
            data={"username": user_name, "password": "UkeV3BNUIL7x/n0J"},
        )
        headers["Authorization"] = f"Bearer {get_token.json().get('access_token')}"
    return headers
