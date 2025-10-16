import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.logging import get_logger, log_handler
from app.models.bed_models import Bed
from app.schemas.bed_schemas import BedCreate, BedRead, BedUpdate

logger = get_logger(__name__)


class BedService:

    def __init__(self, session: AsyncSession):
        self._db = session

    async def create_bed(self, bed: BedCreate) -> Bed:
        """
        Create a new bed in database.

        :param bed: BedCreate object; beds.bed_schemas.BedCreate
        :return: Bed object; beds.bed_models.Bed
        """

        db_bed = Bed(**bed.model_dump())

        start = time.time()

        self._db.add(db_bed)
        await self._db.commit()
        await self._db.refresh(db_bed)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_bed",
            table="bed",
            duration_ms=duration_ms,
            bed_id=str(db_bed.id),
        )
        return db_bed

    async def get_bed(self, bed_id: UUID) -> BedRead:
        """
        Get a Bed object given a bed_id

        :param bed_id: a Bed unique identifier
        :return: BedRead object; beds.bed_schemas.BedRead
        """

        statement = (
            select(Bed)
            .options(
                selectinload(Bed.notes),
                selectinload(Bed.plants),
            )
            .where(Bed.id == bed_id)
        )

        start = time.time()

        result = await self._db.execute(statement)
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

    async def get_beds(
        self, garden_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Bed | None]:
        """
        Get all Bed objects in garden

        :param garden_id: Garden UUID
        :param skip: Number of rows to skip
        :param limit: Number of rows to return
        :return: Sequence[Bed]; beds.bed_models.Bed
        """

        statement = (
            select(Bed).where(Bed.garden_id == garden_id).offset(skip).limit(limit)
        )

        start = time.time()

        result = await self._db.execute(statement)
        beds = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_beds",
            table="bed",
            duration_ms=duration_ms,
            list_length=len(beds),
        )
        return beds

    async def update_bed(self, bed_id: UUID, bed_update: BedUpdate) -> Bed | None:
        """
        Update bed object by bed_id

        :param bed_id: Bed UUID
        :param bed_update: BedUpdate object beds.bed_schema.BedUpdate
        :return: Bed object; beds.bed_models.Bed
        """

        bed: Bed | None = await self._db.get(Bed, bed_id)
        if bed:
            bed_data = bed_update.model_dump(exclude_unset=True)
            for field, value in bed_data.items():
                setattr(bed, field, value)

            start = time.time()

            self._db.add(bed)
            await self._db.commit()
            await self._db.refresh(bed)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_bed",
                table="bed",
                duration_ms=duration_ms,
                bed_id=str(bed.id),
            )
        return bed

    async def delete_bed(self, bed_id: UUID) -> bool:
        """
        Delete bed object by bed_id

        :param bed_id: Bed UUID
        :return: bool
        """

        bed = await self._db.get(Bed, bed_id)
        if bed:
            start = time.time()

            await self._db.delete(bed)
            await self._db.commit()

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_bed",
                table="bed",
                duration_ms=duration_ms,
                bed_id=str(bed_id),
            )
            return True
        return False
