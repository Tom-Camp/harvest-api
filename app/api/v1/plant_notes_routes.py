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
from app.models.plant_models import Plant, PlantNote
from app.schemas.auth_schemas import TokenData
from app.schemas.plant_notes_schemas import (
    PlantNoteCreate,
    PlantNoteList,
    PlantNoteRead,
    PlantNoteUpdate,
)
from app.services.plant_note_service import PlantNoteService

logger = get_logger(__name__)

plant_note_router = APIRouter(prefix="/plant-notes")


def get_plant_note_service() -> PlantNoteService:
    return PlantNoteService(session=AsyncSessionLocal())


@plant_note_router.post("/", response_model=PlantNote)
async def create_plant_note(
    note: PlantNoteCreate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: PlantNoteService = Depends(get_plant_note_service),
    session: AsyncSession = Depends(get_db),
) -> PlantNote:
    """
    Route for creating a plant note.

    :param note: PlantNoteCreate; schemas.plant_note_schemas.PlantNoteCreate
    :param service: PlantNoteService; service.plant_note_service.PlantNoteService
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    :return: PlantNote
    """

    statement = (
        select(Garden.user_id, Garden.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .join(Plant, Bed.id == Plant.bed_id)
        .where(Plant.id == note.plant_id)
    )
    results = await session.execute(statement)
    row = results.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    garden_user, garden_id = row

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:up"
    )

    new_note = await service.create_note(note=note)
    log_handler.log_garden_event(
        event="Create PlantNote",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": garden_id,
            "plant_id": new_note.plant_id,
            "note_id": new_note.id,
            "action": "create_plant_note",
            "resource": "plant_note_routes",
        },
    )

    return new_note


@plant_note_router.get("/{note_id}", response_model=PlantNoteRead)
async def read_plant_note(
    note_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    service: PlantNoteService = Depends(get_plant_note_service),
    session: AsyncSession = Depends(get_db),
) -> PlantNote:
    """
    Route for getting a plant note.

    :param note_id: UUID
    :param current_user: User
    :param service: PlantNoteService; service.plant_note_service.PlantNoteService
    :param session: SQLAlchemy asyncio AsyncSession
    :return: PlantNoteRead; schemas.plant_note_schemas.PlantNoteRead
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    statement = (
        select(Garden.user_id)
        .join(Bed, Garden.id == Bed.garden_id)
        .join(Plant, Bed.id == Plant.bed_id)
        .where(Plant.id == note.plant_id)
    )
    results = await session.execute(statement)
    row = results.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")

    check_garden_access(current_user=current_user, garden_user=row[0], scope="ga:re")

    return note


@plant_note_router.get("/notes/{plant_id}", response_model=list[PlantNoteList])
async def read_plant_notes(
    plant_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    skip: int = 0,
    limit: int = 100,
    service: PlantNoteService = Depends(get_plant_note_service),
    session: AsyncSession = Depends(get_db),
) -> list[PlantNoteList]:
    """
    Route for getting a list of plant notes.

    :param plant_id: UUID
    :param skip: number of rows to skip
    :param limit: limit number of rows to return
    :param service: PlantNoteService; service.plant_note_service.PlantNoteService
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: User
    """

    statement = (
        select(Garden.user_id)
        .join(Bed, Garden.id == Bed.garden_id)
        .join(Plant, Bed.id == Plant.bed_id)
        .where(Plant.id == plant_id)
    )
    result = await session.execute(statement)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")

    check_garden_access(current_user=current_user, garden_user=row[0], scope="ga:re")

    notes = await service.get_notes(plant_id=plant_id, skip=skip, limit=limit)
    return [PlantNoteList.model_validate(note) for note in notes]


@plant_note_router.put("/{note_id}", response_model=PlantNote)
async def update_plant_note(
    note_id: UUID,
    note_update: PlantNoteUpdate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    service: PlantNoteService = Depends(get_plant_note_service),
    session: AsyncSession = Depends(get_db),
) -> PlantNote:
    """
    Route for updating a bed note.

    :param note_id: UUID
    :param note_update: PlantNoteUpdate object; schemas.plant_note_schemas.PlantNoteUpdate
    :param current_user: User
    :param service: PlantNoteService; service.plant_note_service.PlantNoteService
    :param session: SQLAlchemy asyncio AsyncSession
    :return: PlantNote
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    statement = (
        select(Garden.user_id, Garden.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .join(Plant, Bed.id == Plant.bed_id)
        .where(Plant.id == note.plant_id)
    )
    results = await session.execute(statement)
    row = results.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    garden_user, garden_id = row

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:up"
    )

    updated_note = await service.update_note(note_id=note_id, note_update=note_update)
    if updated_note:
        log_handler.log_garden_event(
            event="Update PlantNote",
            context={
                "actor_id": current_user.id,
                "actor_username": current_user.username,
                "garden_id": garden_id,
                "plant_id": updated_note.plant_id,
                "note_id": updated_note.id,
                "action": "update_plant_note",
                "resource": "plant_note_routes",
            },
        )
    return updated_note


@plant_note_router.delete("/{plant_id}")
async def delete_plant_note(
    note_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:de", "ga: de:own"])
    ],
    service: PlantNoteService = Depends(get_plant_note_service),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Route to delete bed note.

    :param note_id: UUID
    :param current_user: User
    :param service: PlantNoteService; service.plant_note_service.PlantNoteService
    :param session: SQLAlchemy asyncio AsyncSession
    :return: dict
    """

    note = await service.get_note(note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    statement = (
        select(Garden.user_id, Garden.id)
        .join(Bed, Garden.id == Bed.garden_id)
        .join(Plant, Bed.id == Plant.bed_id)
        .where(Plant.id == note.plant_id)
    )
    results = await session.execute(statement)
    row = results.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    garden_user, garden_id = row

    check_garden_access(
        current_user=current_user, garden_user=garden_user, scope="ga:de"
    )

    if not await service.delete_note(note_id=note_id):
        raise HTTPException(status_code=404, detail="Note not found")

    log_handler.log_garden_event(
        event="Delete PlantNote",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": garden_id,
            "plant_id": note.plant_id,
            "note_id": note.id,
            "action": "delete_plant_note",
            "resource": "plant_note_routes",
        },
    )

    return {"message": "Note deleted successfully"}
