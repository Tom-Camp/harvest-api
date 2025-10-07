import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.logging import get_logger, log_handler
from app.models.plant_models import Plant
from app.models.recommendation_model import Recommendations
from app.schemas.plant_schemas import PlantCreate, PlantUpdate

logger = get_logger(__name__)


class PlantService:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def create_plant(self, plant: PlantCreate) -> Plant:
        """
        Create a Plant object

        :param plant: PlantCreate object; plants.plant_schemas.PlantCreate
        :return: Plant
        """

        new_plant = Plant(**plant.model_dump())

        start = time.time()

        self._db.add(new_plant)
        await self._db.commit()
        await self._db.refresh(new_plant)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_plant",
            table="plant",
            duration_ms=duration_ms,
            bed_id=str(new_plant.id),
        )
        return new_plant

    async def get_plant(self, plant_id: UUID) -> Plant | None:
        """
        Get a Plant object with Recommendations

        :param plant_id: Plant UUID
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

        result = await self._db.execute(statement)
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

    async def update_plant(
        self, plant_id: UUID, plant_update: PlantUpdate
    ) -> Plant | None:
        """
        Update Plant object by plant_id

        :param plant_id: Plant UUID
        :param plant_update: PlantUpdate object plants.plant_schemas.PlantUpdate
        :return: Plant object
        """

        plant: Plant | None = await self._db.get(Plant, plant_id)
        if plant:
            plant_data = plant_update.model_dump(exclude_unset=True)
            for field, value in plant_data.items():
                setattr(plant, field, value)

            start = time.time()

            self._db.add(plant)
            await self._db.commit()
            await self._db.refresh(plant)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_plant",
                table="plant",
                duration_ms=duration_ms,
                plant_id=str(plant.id),
            )
        return plant

    async def delete_plant(self, plant_id: UUID) -> bool:
        """
        Delete plant object by plant_id

        :param plant_id: plant UUID
        :return: bool
        """

        plant = await self._db.get(Plant, plant_id)
        if plant:
            start = time.time()

            await self._db.delete(plant)
            await self._db.commit()

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_plant",
                table="plant",
                duration_ms=duration_ms,
                plant_id=str(plant_id),
            )
            return True
        return False
