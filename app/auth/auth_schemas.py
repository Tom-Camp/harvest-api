from uuid import UUID

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: UUID
    username: str
    scopes: list[str]


class UserLogin(BaseModel):
    username: str
    password: str
