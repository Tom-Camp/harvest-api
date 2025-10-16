from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.auth.auth import get_current_user
from app.core.utils.database import AsyncSessionLocal, get_db
from app.core.utils.garden_helpers import check_garden_access
from app.logging import get_logger, log_handler
from app.models.bed_models import Bed
from app.models.garden_models import Garden
from app.schemas.auth_schemas import TokenData
from app.schemas.bed_schemas import BedCreate, BedList, BedRead, BedUpdate
from app.services.bed_service import BedService

logger = get_logger(__name__)

bed_router = APIRouter(prefix="/beds")


def get_bed_service() -> BedService:
    return BedService(session=AsyncSessionLocal())


@bed_router.post("", response_model=Bed)
async def create_bed(
    bed: BedCreate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: BedService = Depends(get_bed_service),
    session: AsyncSession = Depends(get_db),
) -> Bed:
    """
    Route to create a new bed.

    :param bed: BedCreate object; schemas.bed_schemas.BedCreate
    :param current_user: The User accessing the route
    :param service: BedService; services.bed_service.BedService
    :param session: SQLAlchemy asyncio AsyncSession
    :return: Bed; beds.bed_models.Bed
    """

    garden = await session.get(Garden, bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    new_bed = await service.create_bed(bed=bed)
    log_handler.log_garden_event(
        event="Create Bed",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": new_bed.garden_id,
            "bed_id": new_bed.id,
            "bed_name": new_bed.name,
            "action": "create_bed",
            "resource": "bed_routes",
        },
    )

    return new_bed


@bed_router.get("/garden/{garden_id}", response_model=list[BedList])
async def read_beds(
    garden_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    skip: int = 0,
    limit: int = 100,
    service: BedService = Depends(get_bed_service),
    session: AsyncSession = Depends(get_db),
) -> list[BedList]:
    """
    Route to get all bed routes associated with a given garden.

    :param garden_id: UUID
    :param skip: rows to skip
    :param limit: limit the number of rows
    :param current_user: The User accessing the route
    :param service: BedService; services.bed_service.BedService
    :param session: SQLAlchemy asyncio AsyncSession
    :return: list[BedList]; schemas.bed_schemas.BedList
    """

    garden = await session.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:re"
    )

    beds = await service.get_beds(garden_id=garden_id, skip=skip, limit=limit)
    return [BedList.model_validate(bed) for bed in beds]


@bed_router.get("/{bed_id}", response_model=BedRead)
async def read_bed(
    bed_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    service: BedService = Depends(get_bed_service),
    session: AsyncSession = Depends(get_db),
) -> BedRead:
    """
    Route to get a bed route associated with a given garden and bed id.

    :param bed_id: Bed UUID
    :param current_user: User
    :param service: BedService; services.bed_service.BedService
    :param session: SQLAlchemy asyncio AsyncSession
    :return: BedRead; schemas.bed_schema.BedRead
    """

    bed = await service.get_bed(bed_id=bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await session.get(Garden, bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_garden_access(
        current_user=current_user, garden_user=garden.user_id, scope="ga:re"
    )

    return bed


@bed_router.put("/{bed_id}", response_model=Bed)
async def update_bed(
    bed_id: UUID,
    bed_update: BedUpdate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: BedService = Depends(get_bed_service),
    session: AsyncSession = Depends(get_db),
) -> Bed | None:
    """
    Route to update a bed

    :param bed_id: Bed UUID
    :param bed_update: BedUpdate object; schemas.bed_schemas.BedUpdate
    :param current_user: User
    :param service: BedService; services.bed_service.BedService
    :param session: SQLAlchemy asyncio AsyncSession
    :return: Bed; models.bed_models.Bed
    """

    statement = (
        select(Garden.user_id, Garden.id, Bed.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .where(Bed.id == bed_id)
    )
    result = await session.execute(statement)
    garden_user, garden_id, bed_id = result.first()

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:up"
    )

    updated_bed = await service.update_bed(bed_id=bed_id, bed_update=bed_update)
    if updated_bed:
        log_handler.log_garden_event(
            event="Updated bed",
            context={
                "actor_id": current_user.id,
                "actor_username": current_user.username,
                "garden_id": updated_bed.garden_id,
                "bed_id": updated_bed.id,
                "bed_name": updated_bed.name,
                "action": "update_bed",
                "resource": "bed_routes",
            },
        )
    return updated_bed


@bed_router.delete("/{bed_id}")
async def delete_bed(
    bed_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:de", "ga:de:own"])
    ],
    service: BedService = Depends(get_bed_service),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Route to delete a bed

    :param bed_id: Bed UUID
    :param current_user: User
    :param service: BedService; services.bed_service.BedService
    :param session: SQLAlchemy asyncio AsyncSession
    :return: dict
    """

    statement = (
        select(Garden.user_id, Garden.id, Bed.id, Bed.name)
        .join(Bed, Garden.id == Bed.garden_id)
        .where(Bed.id == bed_id)
    )
    result = await session.execute(statement)
    garden_user, garden_id, bed_id, bed_name = result.first()

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:up"
    )

    if not await service.delete_bed(bed_id=bed_id):
        raise HTTPException(status_code=404, detail="Bed not found")

    log_handler.log_garden_event(
        event="Delete bed",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": garden_id,
            "bed_id": bed_id,
            "bed_name": bed_name,
            "action": "delete_bed",
            "resource": "bed_routes",
        },
    )

    return {"message": "Bed deleted successfully"}
