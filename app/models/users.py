from typing import List, Optional

from sqlmodel import Field, Relationship

from app.models.model_base import ModelBase


class Role(ModelBase, table=True):  # type: ignore
    name: str = Field(index=True, unique=True)
    description: str | None = None
    users: List["User"] = Relationship(back_populates="role")


class User(ModelBase, table=True):  # type: ignore
    __tablename__ = "users"

    email: str = Field(unique=True, index=True)
    hashed_password: str
    username: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    role_id: str = Field(foreign_key="role.id")
    role: Role = Relationship(back_populates="users")
