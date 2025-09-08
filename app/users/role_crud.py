from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.users.user_models import Role, UserRole
from app.users.user_schemas import RoleCreate


class RoleCRUD:
    @staticmethod
    async def create_role(session: AsyncSession, role: RoleCreate) -> Role:
        db_role = Role(**role.model_dump())
        session.add(db_role)
        await session.commit()
        await session.refresh(db_role)
        return db_role

    @staticmethod
    async def get_role(session: AsyncSession, role_id: UUID) -> Optional[Role]:
        return await session.get(Role, role_id)

    @staticmethod
    async def get_role_by_name(session: AsyncSession, name: str) -> Optional[Role]:
        statement = select(Role).where(Role.__table__.c.name == name)
        result = await session.execute(statement)
        role = result.scalars().first()
        return role

    @staticmethod
    async def get_roles(
        session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Role]:
        statement = select(Role).offset(skip).limit(limit)
        result = await session.execute(statement)
        roles = result.scalars().all()
        return roles

    @staticmethod
    async def assign_role_to_user(
        session: AsyncSession, user_id: UUID, role_id: UUID
    ) -> UserRole:
        statement = select(UserRole).where(
            UserRole.__table__.c.user_id == user_id,
            UserRole.__table__.c.role_id == role_id,
        )
        result = await session.execute(statement)
        existing = result.scalars().first()

        if existing:
            return existing

        user_role = UserRole(user_id=user_id, role_id=role_id)
        session.add(user_role)
        await session.commit()
        await session.refresh(user_role)
        return user_role

    @staticmethod
    async def remove_role_from_user(
        session: AsyncSession,
        user_id: UUID,
        role_id: UUID,
    ) -> bool:
        statement = select(UserRole).where(
            UserRole.__table__.c.user_id == user_id,
            UserRole.__table__.c.role_id == role_id,
        )
        result = await session.execute(statement)
        user_role = result.scalars().first()

        if user_role:
            await session.delete(user_role)
            await session.commit()
            return True
        return False

    @staticmethod
    async def get_user_roles(session: AsyncSession, user_id: UUID) -> Sequence[Role]:
        statement = (
            select(Role).join(UserRole).where(UserRole.__table__.c.user_id == user_id)
        )
        result = await session.execute(statement)
        roles = result.scalars().all()
        return roles
