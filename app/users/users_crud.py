from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.auth.auth import get_password_hash
from app.logging import get_logger
from app.users.user_models import User, UserRole
from app.users.user_schemas import UserCreate, UserReadWithRoles, UserUpdate

logger = get_logger(__name__)


class UserCRUD:
    @staticmethod
    async def create_user(session: AsyncSession, user: UserCreate) -> User:
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            hashed_password=hashed_password,
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user

    @staticmethod
    async def get_user(session: AsyncSession, user_id: UUID) -> User | None:
        return await session.get(User, user_id)

    @staticmethod
    async def get_user_with_roles(
        session: AsyncSession,
        user_id: UUID,
    ) -> UserReadWithRoles | None:
        statement = (
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.id == user_id)
        )
        result = await session.execute(statement)
        user = result.scalars().first()
        logger.debug("User: %s" % user.username)
        return UserReadWithRoles(**user.model_dump())

    @staticmethod
    async def get_user_by_username(
        session: AsyncSession, username: str
    ) -> Optional[User]:
        statement = select(User).where(User.__table__.c.username == username)
        result = await session.execute(statement)
        return result.scalars().first()

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        statement = select(User).where(User.__table__.c.email == email)
        result = await session.execute(statement)
        return result.scalars().first()

    @staticmethod
    async def get_users(
        session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[User]:
        """Get users with pagination"""
        statement = select(User).offset(skip).limit(limit)
        result = await session.execute(statement)
        users = result.scalars().all()
        return users

    @staticmethod
    async def update_user(
        session: AsyncSession, user_id: UUID, user_update: UserUpdate
    ) -> Optional[User]:
        user = await session.get(User, user_id)
        if user:
            user_data = user_update.model_dump(exclude_unset=True)
            for field, value in user_data.items():
                setattr(user, field, value)
            user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

    @staticmethod
    async def delete_user(session: AsyncSession, user_id: UUID) -> bool:
        user = await session.get(User, user_id)
        if user:
            await session.delete(user)
            await session.commit()
            return True
        return False
