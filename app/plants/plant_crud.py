import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.logging import get_logger, log_handler
from app.plants.plant_models import Plant
from app.plants.plant_schema import PlantCreate, PlantUpdate
from app.plants.recommendation_model import Recommendations

logger = get_logger(__name__)


class PlantCRUD:

    @staticmethod
    async def create_plant(
        plant: PlantCreate,
        session: AsyncSession,
    ) -> Plant:
        """
        Create a Plant object

        :param plant: PlantCreate object; plants.plant_schemas.PlantCreate
        :param session: SQLAlchemy asyncio AsyncSession
        :return: Plant
        """

        new_plant = Plant(**plant.model_dump())

        start = time.time()

        session.add(new_plant)
        await session.commit()
        await session.refresh(new_plant)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_plant",
            table="plant",
            duration_ms=duration_ms,
            bed_id=str(new_plant.id),
        )
        return new_plant

    @staticmethod
    async def get_plant(session: AsyncSession, plant_id: UUID) -> Plant | None:
        """
        Get a Plant object with Recommendations

        :param plant_id: Plant UUID
        :param session: SQLAlchemy asyncio AsyncSession
        :return: Plant; plants.plant_models.Plant
        """

        statement = (
            select(Plant)
            .options(
                selectinload(Plant.notes),
                selectinload(Plant.harvest),
                selectinload(Plant.recommendations).selectinload(
                    Recommendations.growing_tips
                ),
                selectinload(Plant.recommendations).selectinload(
                    Recommendations.planting_window
                ),
                selectinload(Plant.recommendations).selectinload(
                    Recommendations.care_instructions
                ),
                selectinload(Plant.recommendations).selectinload(Recommendations.pests),
            )
            .where(Plant.id == plant_id)
        )

        start = time.time()

        result = await session.execute(statement)
        plant = result.scalars().first()
        pid = str(plant.id) if isinstance(plant, Plant) else "none"

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_plant",
            table="plants",
            duration_ms=duration_ms,
            plant_id=pid,
        )
        return plant

    @staticmethod
    async def update_plant(
        session: AsyncSession, plant_id: UUID, plant_update: PlantUpdate
    ) -> Plant | None:
        """
        Update Plant object by plant_id

        :param session: SQLAlchemy asyncio AsyncSession
        :param plant_id: Plant UUID
        :param plant_update: PlantUpdate object plants.plant_schemas.PlantUpdate
        :return: Plant object
        """
        plant: Plant | None = await session.get(Plant, plant_id)
        if plant:
            plant_data = plant_update.model_dump(exclude_unset=True)
            for field, value in plant_data.items():
                setattr(plant, field, value)

            start = time.time()

            session.add(plant)
            await session.commit()
            await session.refresh(plant)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_plant",
                table="plant",
                duration_ms=duration_ms,
                plant_id=str(plant.id),
            )
        return plant
