from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.model_base import ModelBase
from app.users.user_models import Role, UserBase


class UserCreate(BaseModel):
    password: str
    username: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    email: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRole(BaseModel):
    role: Role


class UserRead(ModelBase, UserBase):
    id: UUID
    email: str
    username: str
    first_name: str | None = None
    last_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserReadPublic(ModelBase, UserBase):
    username: str
    first_name: str | None = None
    last_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserScopes(BaseModel):
    id: UUID
    username: str
    scopes: list[str]
