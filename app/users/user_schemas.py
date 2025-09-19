from sqlmodel import SQLModel

from app.helpers.model_base import ModelBase
from app.users.user_models import UserBase


class UserCreate(UserBase):
    password: str
    location: str
    first_name: str | None = None
    last_name: str | None = None


class UserUpdate(SQLModel):
    email: str | None = None
    username: str | None = None
    location: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class UserRead(ModelBase, UserBase):
    email: str
    username: str
    first_name: str | None = None
    last_name: str | None = None
