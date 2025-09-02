from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.users import Role


class UserCreate(SQLModel):
    email: str
    username: str
    hashed_password: str
    full_name: Optional[str] = None
    role: Role


class UserUpdate(SQLModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(SQLModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    created_date: datetime
    updated_date: datetime
    role: Role


class UserPublic(SQLModel):
    id: str
    username: str
    full_name: Optional[str]
    is_active: bool
