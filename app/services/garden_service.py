import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.logging import get_logger, log_handler
from app.models.garden_models import Garden
from app.models.user_models import User
from app.schemas.garden_schemas import GardenCreate, GardenUpdate

logger = get_logger(__name__)


class GardenService:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def create_garden(self, garden: GardenCreate, user: User) -> Garden:
        """
        Create a new Garden

        :param garden: GardenCreate object; gardens.garden_schemas.GardenCreate
        :param user: User object; users.user_models.User
        :return: Garden object; gardens.garden_models.Garden
        """

        start = time.time()

        db_garden = Garden(**garden.model_dump(), user=user)
        self._db.add(db_garden)
        await self._db.commit()
        await self._db.refresh(db_garden)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_garden",
            table="garden",
            duration_ms=duration_ms,
            garden_id=str(db_garden.id),
        )
        return db_garden

    async def get_garden(self, garden_id: UUID) -> Garden:
        """
        Get a Garden by ID

        :param garden_id: UUID
        :return: Garden object; garden.garden_models.Garden
        """

        statement = (
            select(Garden)
            .options(
                selectinload(Garden.beds),
                selectinload(Garden.user),
                selectinload(Garden.notes),
            )
            .where(Garden.id == garden_id)
        )
        start = time.time()

        result = await self._db.execute(statement)
        garden = result.scalars().first()

        duration_ms = (time.time() - start) * 1000
        gid = str(garden.id) if isinstance(garden, Garden) else "none"

        log_handler.log_database_operation(
            operation="get_garden",
            table="garden",
            duration_ms=duration_ms,
            garden_id=gid,
        )
        return garden

    async def get_gardens(self, skip: int = 0, limit: int = 100) -> Sequence[Garden]:
        """
        Get all Gardens

        :param skip: the rows to skip
        :param limit: the number of rows to return
        :return: list of Garden objects; garden.garden_models.Garden
        """

        statement = select(Garden).offset(skip).limit(limit)

        start = time.time()

        result = await self._db.execute(statement)
        garden = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_gardens",
            table="garden",
            duration_ms=duration_ms,
            list_length=len(garden),
        )
        return garden

    async def get_user_gardens(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Garden]:
        """
        Get all Gardens for a given user

        :param user_id: The ID for the user
        :param skip: the rows to skip
        :param limit: the number of rows to return
        :return: list of Garden objects; garden.garden_models.Garden
        """

        statement = (
            select(Garden).where(Garden.user_id == user_id).offset(skip).limit(limit)
        )

        start = time.time()

        result = await self._db.execute(statement)
        gardens = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_user_gardens",
            table="garden",
            duration_ms=duration_ms,
            user_id=user_id,
            list_length=len(gardens),
        )
        return gardens

    async def update_garden(
        self, garden_id: UUID, garden_update: GardenUpdate
    ) -> Garden | None:
        """
        Update a Garden by ID

        :param garden_id: The ID of the garden to update
        :param garden_update: The GardenUpdate object; gardens.garden_schemas.GardenUpdate
        :return: Garden object; garden.garden_models.Garden
        """

        garden: Garden | None = await self._db.get(Garden, garden_id)
        if garden:
            garden_data = garden_update.model_dump(exclude_unset=True)
            for field, value in garden_data.items():
                setattr(garden, field, value)

            start = time.time()

            self._db.add(garden)
            await self._db.commit()
            await self._db.refresh(garden)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_garden",
                table="garden",
                duration_ms=duration_ms,
                garden_id=str(garden.id),
            )
        return garden

    async def delete_garden(self, garden_id: UUID) -> bool:
        """
        Delete a garden

        :param garden_id: The ID of the garden to delete
        :return: boolean
        """

        return_value: bool = False
        garden = await self._db.get(Garden, garden_id)
        if garden:
            start = time.time()

            await self._db.delete(garden)
            await self._db.commit()
            return_value = True

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_garden",
                table="garden",
                duration_ms=duration_ms,
                garden_id=str(garden.id),
            )
        return return_value
