import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.beds.bed_models import Bed
from app.beds.bed_schemas import BedCreate, BedUpdate
from app.logging import get_logger, log_handler

logger = get_logger(__name__)


class BedCRUD:

    @staticmethod
    async def create_bed(
        bed: BedCreate,
        session: AsyncSession,
    ) -> Bed:
        db_bed = Bed(**bed.model_dump())

        start = time.time()

        session.add(db_bed)
        await session.commit()
        await session.refresh(db_bed)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_bed",
            table="bed",
            duration_ms=duration_ms,
            bed_id=str(db_bed.id),
        )
        return db_bed

    @staticmethod
    async def get_bed(session: AsyncSession, bed_id: UUID) -> Bed | None:
        statement = select(Bed).options(selectinload(Bed.notes)).where(Bed.id == bed_id)

        start = time.time()

        result = await session.execute(statement)
        bed = result.scalars().first()
        bid = str(bed.id) if isinstance(bed, Bed) else "none"

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_bed",
            table="bed",
            duration_ms=duration_ms,
            bed_id=bid,
        )
        return bed

    @staticmethod
    async def get_beds(
        garden_id: UUID, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Bed]:
        statement = (
            select(Bed).where(Bed.garden_id == garden_id).offset(skip).limit(limit)
        )

        start = time.time()

        result = await session.execute(statement)
        beds = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_beds",
            table="bed",
            duration_ms=duration_ms,
            list_length=len(beds),
        )
        return beds

    @staticmethod
    async def update_bed(
        session: AsyncSession, bed_id: UUID, bed_update: BedUpdate
    ) -> Bed | None:
        bed: Bed | None = await session.get(Bed, bed_id)
        if bed:
            bed_data = bed_update.model_dump(exclude_unset=True)
            for field, value in bed_data.items():
                setattr(bed, field, value)

            start = time.time()

            session.add(bed)
            await session.commit()
            await session.refresh(bed)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_bed",
                table="bed",
                duration_ms=duration_ms,
                bed_id=str(bed.id),
            )
        return bed

    @staticmethod
    async def delete_bed(session: AsyncSession, bed_id: UUID) -> bool:
        bed = await session.get(Bed, bed_id)
        if bed:
            start = time.time()

            await session.delete(bed)
            await session.commit()

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_bed",
                table="bed",
                duration_ms=duration_ms,
                bed_id=str(bed_id),
            )
            return True
        return False
