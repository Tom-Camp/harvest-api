import base64
import binascii

from fastapi import Request
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
)


class BasicAuth(AuthenticationBackend):
    async def authenticate(
        self, request: Request
    ) -> tuple[AuthCredentials, SimpleUser] | None:
        if "Authorization" not in request.headers:
            return None
        auth = request.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            raise AuthenticationError("Invalid basic auth credentials")
        username, _, _ = decoded.partition(":")
        return AuthCredentials(["authenticated"]), SimpleUser(username)
