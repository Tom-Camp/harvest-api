import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.gardens.garden_models import Garden
from app.gardens.garden_schemas import GardenCreate, GardenUpdate
from app.logging import get_logger, log_handler
from app.users.user_models import User

logger = get_logger(__name__)


class GardenCRUD:

    @staticmethod
    async def create_garden(
        garden: GardenCreate, session: AsyncSession, user: User
    ) -> Garden:
        """
        Create a new Garden

        :param garden: GardenCreate object; gardens/garden_schemas.py
        :param session: SQLAlchemy asyncio AsyncSession
        :param user: User object
        :return: Garden object
        """

        start = time.time()

        db_garden = Garden(**garden.model_dump(), user=user)
        session.add(db_garden)
        await session.commit()
        await session.refresh(db_garden)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_garden",
            table="garden",
            duration_ms=duration_ms,
            garden_id=str(db_garden.id),
        )
        return db_garden

    @staticmethod
    async def get_garden(session: AsyncSession, garden_id: UUID) -> Garden:
        """
        Get a Garden by ID

        :param session: SQLAlchemy asyncio AsyncSession
        :param garden_id: UUID
        :return: Garden object
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

        result = await session.execute(statement)
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

    @staticmethod
    async def get_gardens(
        session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Garden]:
        """
        Get all Gardens

        :param session: SQLAlchemy asyncio AsyncSession
        :param skip: the rows to skip
        :param limit: the number of rows to return
        :return: list of Garden objects
        """

        statement = select(Garden).offset(skip).limit(limit)

        start = time.time()

        result = await session.execute(statement)
        garden = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_gardens",
            table="garden",
            duration_ms=duration_ms,
            list_length=len(garden),
        )
        return garden

    @staticmethod
    async def get_user_gardens(
        session: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Garden]:
        """
        Get all Gardens for a given user

        :param session: SQLAlchemy asyncio AsyncSession
        :param user_id: The ID for the user
        :param skip: the rows to skip
        :param limit: the number of rows to return
        :return: list of Garden objects
        """

        statement = (
            select(Garden).where(Garden.user_id == user_id).offset(skip).limit(limit)
        )

        start = time.time()

        result = await session.execute(statement)
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

    @staticmethod
    async def update_garden(
        session: AsyncSession, garden_id: UUID, garden_update: GardenUpdate
    ) -> Garden | None:
        """
        Update a Garden by ID

        :param session: SQLAlchemy asyncio AsyncSession
        :param garden_id: The ID of the garden to update
        :param garden_update: The GardenUpdate object; gardens/garden_schemas.py
        :return: Garden object
        """

        garden: Garden | None = await session.get(Garden, garden_id)
        if garden:
            garden_data = garden_update.model_dump(exclude_unset=True)
            for field, value in garden_data.items():
                setattr(garden, field, value)

            start = time.time()

            session.add(garden)
            await session.commit()
            await session.refresh(garden)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_garden",
                table="garden",
                duration_ms=duration_ms,
                garden_id=str(garden.id),
            )
        return garden

    @staticmethod
    async def delete_garden(session: AsyncSession, garden_id: UUID) -> bool:
        """
        Delete a garden

        :param session: SQLAlchemy asyncio AsyncSession
        :param garden_id: The ID of the garden to delete
        :return: boolean
        """

        return_value: bool = False
        garden = await session.get(Garden, garden_id)
        if garden:
            start = time.time()

            await session.delete(garden)
            await session.commit()
            return_value = True

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_garden",
                table="garden",
                duration_ms=duration_ms,
                garden_id=str(garden.id),
            )
        return return_value
