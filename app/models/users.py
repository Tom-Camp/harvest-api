import uuid

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from fastapi_users.schemas import BaseUser, BaseUserCreate
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, get_async_session


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass


class UserCreate(BaseUserCreate):
    pass


class UserRead(BaseUser[uuid.UUID]):
    pass


class UserUpdate(BaseUserCreate):
    pass


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    pass


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
