from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_user
from app.auth.auth_schemas import TokenData
from app.beds.bed_crud import BedCRUD
from app.beds.bed_models import Bed
from app.beds.bed_schemas import BedCreate, BedList, BedRead, BedUpdate
from app.core.auth.scopes_manager import ScopesManager
from app.gardens.garden_crud import GardenCRUD
from app.logging import get_logger, log_handler
from app.utils.database import get_db

logger = get_logger(__name__)

bed_router = APIRouter(prefix="/beds")


def check_access(current_user: TokenData, garden_user: UUID, scope: str):

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope=scope
    )
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope=f"{scope}:own",
        user_id=current_user.id,
        entity_owner=garden_user,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")


@bed_router.post("", response_model=Bed)
async def create_bed(
    bed: BedCreate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    session: AsyncSession = Depends(get_db),
) -> Bed:
    """
    Route to create a new bed in casbin.

    :param bed: BedCreate object; beds.bed_schemas.BedCreate
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: The User accessing the route
    :return: Bed; beds.bed_models.Bed
    """

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    new_bed = await BedCRUD.create_bed(
        bed=bed,
        session=session,
    )
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
    session: AsyncSession = Depends(get_db),
) -> list[BedList]:
    """
    Route to get all bed routes associated with a given garden.

    :param garden_id: UUID
    :param skip: rows to skip
    :param limit: limit the number of rows
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: The User accessing the route
    :return: list[BedList]; beds.bed_schema.BedList
    """

    garden = await GardenCRUD.get_garden(session=session, garden_id=garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_access(current_user=current_user, garden_user=garden.user_id, scope="ga:re")

    beds = await BedCRUD.get_beds(
        garden_id=garden_id,
        session=session,
        skip=skip,
        limit=limit,
    )
    return [BedList.model_validate(bed) for bed in beds]


@bed_router.get("/{bed_id}", response_model=BedRead)
async def read_bed(
    bed_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    session: AsyncSession = Depends(get_db),
) -> BedRead:
    """
    Route to get a bed route associated with a given garden and bed id.

    :param bed_id: Bed UUID
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: BedRead; beds.bed_schema.BedRead
    """

    bed = await BedCRUD.get_bed(session=session, bed_id=bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_access(current_user=current_user, garden_user=garden.user_id, scope="ga:re")

    return bed


@bed_router.put("/{bed_id}", response_model=Bed)
async def update_bed(
    bed_id: UUID,
    bed_update: BedUpdate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    session: AsyncSession = Depends(get_db),
) -> Bed | None:
    """
    Route to update a bed

    :param bed_id: Bed UUID
    :param bed_update: BedUpdate object; beds.bed_schemas.BedUpdate
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: Bed; beds.bed_models.Bed
    """

    bed = await BedCRUD.get_bed(session=session, bed_id=bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_access(current_user=current_user, garden_user=garden.user_id, scope="ga:up")

    updated_bed = await BedCRUD.update_bed(
        session=session,
        bed_id=bed_id,
        bed_update=bed_update,
    )
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
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Route to delete a bed

    :param bed_id: Bed UUID
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: dict
    """

    bed = await BedCRUD.get_bed(session=session, bed_id=bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    check_access(current_user=current_user, garden_user=garden.user_id, scope="ga:de")

    if not await BedCRUD.delete_bed(session, bed_id):
        raise HTTPException(status_code=404, detail="Bed not found")

    log_handler.log_garden_event(
        event="Delete bed",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": bed.garden_id,
            "bed_id": bed.id,
            "bed_name": bed.name,
            "action": "delete_bed",
            "resource": "bed_routes",
        },
    )

    return {"message": "Bed deleted successfully"}
