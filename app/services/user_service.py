import time
from typing import Sequence
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.auth.auth_helpers import get_password_hash
from app.logging import get_logger, log_handler
from app.models.role_models import Role
from app.models.user_models import User
from app.schemas.user_schemas import UserCreate, UserUpdate

logger = get_logger(__name__)


class UserService:

    def __init__(self, session: AsyncSession):
        self._db = session

    async def create_user(self, user: UserCreate) -> User:
        """
        Create a new user

        :param user: The UserCreate object; users.user_schemas.UserCreate
        :return: User object
        """

        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
        )

        statement = select(Role).where(Role.name == "authenticated")
        result = await self._db.execute(statement)
        auth_role = result.scalars().first()
        if auth_role:
            db_user.roles.append(auth_role)

        start = time.time()

        self._db.add(db_user)
        await self._db.commit()
        await self._db.refresh(db_user)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_user",
            table="user",
            duration_ms=duration_ms,
            user_id=str(db_user.id),
        )
        return db_user

    async def get_user(self, user_id: UUID) -> User | None:
        """
        Get a user

        :param user_id: The user's unique ID
        :return: User object
        """
        start = time.time()

        user = await self._db.get(User, user_id)
        uid = str(user.id) if isinstance(user, User) else "none"

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_user",
            table="user",
            duration_ms=duration_ms,
            user_id=uid,
        )

        return user

    async def get_user_with_roles(self, user_id: UUID) -> User | None:
        """
        Get a user by username

        :param user_id: The user's unique ID
        :return: The User or None
        """

        statement = (
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )

        start = time.time()

        result = await self._db.execute(statement)
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

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Get a user by username

        :param username: The username
        :return: The User or None
        """

        statement = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.username == username)
        )

        start = time.time()

        result = await self._db.execute(statement)
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

    async def get_user_by_email(self, email: EmailStr) -> User | None:
        """
        Get a user by email

        :param email: The email
        :return: The User or None
        """

        statement = select(User).where(User.email == email)

        start = time.time()

        result = await self._db.execute(statement)
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

    async def get_users(self, skip: int = 0, limit: int = 100) -> Sequence[User | None]:
        """
        Get all users

        :param skip: The number of users to skip
        :param limit: The number of users to return
        :return: The list of Users
        """

        statement = select(User).offset(skip).limit(limit)

        start = time.time()

        result = await self._db.execute(statement)
        users = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_users",
            table="user",
            duration_ms=duration_ms,
            list_length=len(users),
        )
        return users

    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> User | None:
        """
        Update a user

        :param user_id: The UUID of the user
        :param user_update: The UserUpdate object
        :return: The User or None
        """

        user = await self._db.get(User, user_id)
        if user:
            user_data = user_update.model_dump(exclude_unset=True)
            for field, value in user_data.items():
                setattr(user, field, value)

            start = time.time()

            self._db.add(user)
            await self._db.commit()
            await self._db.refresh(user)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_user",
                table="user",
                duration_ms=duration_ms,
                user_id=str(user.id),
            )
        return user

    async def add_user_role(self, user_id: UUID, role: Role) -> User:
        """
        Update a user

        :param user_id: The UUID of the user
        :param role: The UserUpdateRole object
        :return: The User or None
        """

        start = time.time()
        logger.info(f"ROLE: {role.name}")
        statement = (
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )

        result = await self._db.execute(statement)
        user = result.scalars().first()
        if user:
            user.roles.append(role)

            self._db.add(user)
            await self._db.commit()
            await self._db.refresh(user)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="add_user_role",
                table="user",
                duration_ms=duration_ms,
                user_id=str(user.id),
            )
        return user

    async def remove_user_role(self, user_id: UUID, role: Role) -> User:
        """
        Update a user

        :param user_id: The UUID of the user
        :param role: The UserUpdateRole object
        :return: The User or None
        """

        user = await self._db.get(User, user_id)
        if user:
            user.roles.remove(role)

            start = time.time()

            self._db.add(user)
            await self._db.commit()
            await self._db.refresh(user)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="remove_user_role",
                table="user",
                duration_ms=duration_ms,
                user_id=str(user.id),
            )
        return user

    async def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user

        :param user_id: The UUID of the user
        :return: bool
        """
        user = await self._db.get(User, user_id)
        if not isinstance(user, User):
            return False

        start = time.time()

        await self._db.delete(user)
        await self._db.commit()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="delete_user",
            table="user",
            duration_ms=duration_ms,
            user_id=str(user.id),
        )
        return True
