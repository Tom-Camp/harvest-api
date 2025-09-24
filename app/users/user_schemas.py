from pydantic import BaseModel

from app.helpers.model_base import ModelBase
from app.users.user_models import UserBase


class UserCreate(BaseModel):
    password: str
    username: str
    email: str
    first_name: str | None = None
    last_name: str | None = None


class UserUpdate(BaseModel):
    email: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class UserRead(ModelBase, UserBase):
    email: str
    username: str
    first_name: str | None = None
    last_name: str | None = None
