import time
from typing import Sequence
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth.auth import get_password_hash
from app.logging import get_logger, log_handler
from app.users.user_models import User
from app.users.user_schemas import UserCreate, UserUpdate

logger = get_logger(__name__)


class UserCRUD:
    @staticmethod
    async def create_user(session: AsyncSession, user: UserCreate) -> User:
        start = time.time()

        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create user",
            table="user",
            duration_ms=duration_ms,
            user_id=str(db_user.id),
        )
        return db_user

    @staticmethod
    async def get_user(session: AsyncSession, user_id: UUID) -> User | None:
        start = time.time()

        user = await session.get(User, user_id)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get user",
            table="user",
            duration_ms=duration_ms,
            user_id=str(user.id),
        )

        return user

    @staticmethod
    async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
        start = time.time()

        statement = select(User).where(User.username == username)
        result = await session.execute(statement)
        user = result.scalars().first()
        uid = str(user.id) if isinstance(user, User) else "none"

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get user by username",
            table="user",
            duration_ms=duration_ms,
            user_id=uid,
        )
        return user

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: EmailStr) -> User | None:
        start = time.time()

        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        user = result.scalars().first()
        uid = str(user.id) if isinstance(user, User) else "none"

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get user by email",
            table="user",
            duration_ms=duration_ms,
            user_id=uid,
        )
        return user

    @staticmethod
    async def get_users(
        session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[User]:
        start = time.time()

        statement = select(User).offset(skip).limit(limit)
        result = await session.execute(statement)
        users = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get users",
            table="user",
            duration_ms=duration_ms,
            list_length=len(users),
        )
        return users

    @staticmethod
    async def update_user(
        session: AsyncSession, user_id: UUID, user_update: UserUpdate
    ) -> User | None:
        start = time.time()

        user = await session.get(User, user_id)
        if user:
            user_data = user_update.model_dump(exclude_unset=True)
            for field, value in user_data.items():
                setattr(user, field, value)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get user",
            table="user",
            duration_ms=duration_ms,
            user_id=str(user.id),
        )
        return user

    @staticmethod
    async def delete_user(session: AsyncSession, user_id: UUID) -> bool:
        start = time.time()

        user = await session.get(User, user_id)
        if not isinstance(user, User):
            return False
        await session.delete(user)
        await session.commit()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="delete user",
            table="user",
            duration_ms=duration_ms,
            user_id=str(user.id),
        )
        return True
