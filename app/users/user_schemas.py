from sqlmodel import SQLModel

from app.helpers.model_base import ModelBase
from app.users.user_models import UserBase


class UserCreate(UserBase):
    password: str


class UserUpdate(SQLModel):
    email: str | None = None
    username: str | None = None
    full_name: str | None = None


class UserRead(ModelBase, UserBase):
    pass
