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
        """
        Create a new user

        :param session: The SQLAlchemy asyncio AsyncSession
        :param user: The UserCreate object; users.user_schemas.UserCreate
        :return: User
        """

        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
        )

        start = time.time()

        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_user",
            table="user",
            duration_ms=duration_ms,
            user_id=str(db_user.id),
        )
        return db_user

    @staticmethod
    async def get_user(session: AsyncSession, user_id: UUID) -> User:
        """
        Get a user

        :param session: The SQLAlchemy asyncio AsyncSession
        :param user_id: The UUID of the user
        :return: The User or None
        """
        start = time.time()

        user = await session.get(User, user_id)
        uid = str(user.id) if isinstance(user, User) else "none"

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_user",
            table="user",
            duration_ms=duration_ms,
            user_id=uid,
        )

        return user

    @staticmethod
    async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
        """
        Get a user by username

        :param session: The SQLAlchemy asyncio AsyncSession
        :param username: The username
        :return: The User or None
        """

        statement = select(User).where(User.username == username)

        start = time.time()

        result = await session.execute(statement)
        user = result.scalars().first()
        uid = str(user.id) if isinstance(user, User) else "none"

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_user_by_username",
            table="user",
            duration_ms=duration_ms,
            user_id=uid,
        )
        return user

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: EmailStr) -> User | None:
        """
        Get a user by email

        :param session: The SQLAlchemy asyncio AsyncSession
        :param email: The email
        :return: The User or None
        """

        statement = select(User).where(User.email == email)

        start = time.time()

        result = await session.execute(statement)
        user = result.scalars().first()
        uid = str(user.id) if isinstance(user, User) else "none"

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_user_by_email",
            table="user",
            duration_ms=duration_ms,
            user_id=uid,
        )
        return user

    @staticmethod
    async def get_users(
        session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[User]:
        """
        Get all users

        :param session: The SQLAlchemy asyncio AsyncSession
        :param skip: The number of users to skip
        :param limit: The number of users to return
        :return: The list of Users
        """

        statement = select(User).offset(skip).limit(limit)

        start = time.time()

        result = await session.execute(statement)
        users = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_users",
            table="user",
            duration_ms=duration_ms,
            list_length=len(users),
        )
        return users

    @staticmethod
    async def update_user(
        session: AsyncSession, user_id: UUID, user_update: UserUpdate
    ) -> User:
        """
        Update a user

        :param session: The SQLAlchemy asyncio AsyncSession
        :param user_id: The UUID of the user
        :param user_update: The UserUpdate object
        :return: The User or None
        """

        user = await session.get(User, user_id)
        if user:
            user_data = user_update.model_dump(exclude_unset=True)
            for field, value in user_data.items():
                setattr(user, field, value)

            start = time.time()

            session.add(user)
            await session.commit()
            await session.refresh(user)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_user",
                table="user",
                duration_ms=duration_ms,
                user_id=str(user.id),
            )
        return user

    @staticmethod
    async def delete_user(session: AsyncSession, user_id: UUID) -> bool:
        """
        Delete a user

        :param session: The SQLAlchemy asyncio AsyncSession
        :param user_id: The UUID of the user
        :return: bool
        """
        user = await session.get(User, user_id)
        if not isinstance(user, User):
            return False

        start = time.time()

        await session.delete(user)
        await session.commit()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="delete_user",
            table="user",
            duration_ms=duration_ms,
            user_id=str(user.id),
        )
        return True
