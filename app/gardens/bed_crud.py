from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.gardens.bed_models import Bed
from app.gardens.bed_schemas import BedCreate, BedUpdate
from app.logging import get_logger

logger = get_logger(__name__)


class BedCRUD:

    @staticmethod
    async def create_bed(
        bed: BedCreate,
        session: AsyncSession,
    ) -> Bed:
        db_bed = Bed(**bed.model_dump())
        session.add(db_bed)
        await session.commit()
        await session.refresh(db_bed)
        return db_bed

    @staticmethod
    async def get_bed(session: AsyncSession, bed_id: UUID) -> Optional[Bed]:
        statement = (
            select(Bed)
            .options(selectinload(Bed.__table__.c.notes))
            .where(Bed.__table__.c.id == bed_id)
        )
        result = await session.execute(statement)
        bed = result.scalars().first()
        return bed

    @staticmethod
    async def get_beds(
        garden_id: UUID, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Bed]:
        statement = (
            select(Bed)
            .where(Bed.__table__.c.garden_id == garden_id)
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(statement)
        bed = result.scalars().all()
        return bed

    @staticmethod
    async def update_bed(
        session: AsyncSession, bed_id: UUID, bed_update: BedUpdate
    ) -> Bed | None:
        bed: Bed | None = await session.get(Bed, bed_id)
        if bed:
            bed_data = bed_update.model_dump(exclude_unset=True)
            for field, value in bed_data.items():
                setattr(bed, field, value)
            bed.update_timestamp()
            session.add(bed)
            await session.commit()
            await session.refresh(bed)
        return bed

    @staticmethod
    async def delete_bed(session: AsyncSession, bed_id: UUID) -> bool:
        bed = await session.get(Bed, bed_id)
        if bed:
            await session.delete(bed)
            await session.commit()
            return True
        return False
