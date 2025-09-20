from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.gardens.garden_models import Garden
from app.gardens.garden_schemas import GardenCreate, GardenUpdate
from app.logging import get_logger

logger = get_logger(__name__)


class GardenCRUD:

    @staticmethod
    async def create_garden(
        garden: GardenCreate, session: AsyncSession, user_id: UUID
    ) -> Garden:
        db_garden = Garden(**garden.model_dump(), user_id=user_id)
        session.add(db_garden)
        await session.commit()
        await session.refresh(db_garden)
        return db_garden

    @staticmethod
    async def get_garden(session: AsyncSession, garden_id: UUID) -> Optional[Garden]:
        return await session.get(Garden, garden_id)

    @staticmethod
    async def get_gardens(
        session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Garden]:
        statement = select(Garden).offset(skip).limit(limit)
        result = await session.execute(statement)
        garden = result.scalars().all()
        return garden

    @staticmethod
    async def get_user_gardens(
        session: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Garden]:
        statement = (
            select(Garden)
            .where(Garden.__table__.c.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(statement)
        gardens = result.scalars().all()
        return gardens

    @staticmethod
    async def update_garden(
        session: AsyncSession, garden_id: UUID, garden_update: GardenUpdate
    ) -> Garden | None:
        garden: Garden | None = await session.get(Garden, garden_id)
        if garden:
            garden_data = garden_update.model_dump(exclude_unset=True)
            for field, value in garden_data.items():
                setattr(garden, field, value)
            garden.update_timestamp()
            session.add(garden)
            await session.commit()
            await session.refresh(garden)
        return garden

    @staticmethod
    async def delete_garden(session: AsyncSession, garden_id: UUID) -> bool:
        garden = await session.get(Garden, garden_id)
        if garden:
            await session.delete(garden)
            await session.commit()
            return True
        return False
