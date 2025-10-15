from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_user
from app.auth.auth_schemas import TokenData
from app.core.auth.scopes_manager import ScopesManager
from app.gardens.garden_crud import GardenCRUD
from app.gardens.garden_models import GardenNote
from app.gardens.garden_note_crud import GardenNoteCRUD
from app.gardens.garden_note_schemas import (
    GardenNoteCreate,
    GardenNoteList,
    GardenNoteUpdate,
)
from app.logging import get_logger, log_handler
from app.utils.database import get_db

logger = get_logger(__name__)

garden_note_router = APIRouter(prefix="/garden-notes")


@garden_note_router.post("/", response_model=GardenNote)
async def create_garden_note(
    note: GardenNoteCreate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    session: AsyncSession = Depends(get_db),
) -> GardenNote:
    """
    A Route to create a GardenNote

    :param note: The GardenNoteCreate object; gardens.garden_note_schema.GardenNoteCreate
    :param session: The SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :return: GardenNote; gardens.garden_models.GardenNote
    """

    garden = await GardenCRUD.get_garden(session=session, garden_id=note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope="ga:up"
    )
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope="ga:up:own",
        user_id=current_user.id,
        entity_owner=garden.user_id,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")

    new_note = await GardenNoteCRUD.create_note(
        note=note,
        session=session,
    )
    log_handler.log_garden_event(
        event="Note create",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": new_note.garden_id,
            "note_id": new_note.id,
            "action": "create_garden_note",
            "resource": "garden_note_routes",
        },
    )

    return new_note


@garden_note_router.get("/{note_id}", response_model=GardenNote)
async def read_garden_note(
    note_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    session: AsyncSession = Depends(get_db),
) -> GardenNote:
    """
    Route to get a GardenNote

    :param note_id: The note object ID
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :return: A GardenNote; gardens.garden_models.GardenNote
    """

    note = await GardenNoteCRUD.get_note(note_id=note_id, session=session)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope="ga:re"
    )
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope="ga:re:own",
        user_id=current_user.id,
        entity_owner=garden.user_id,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")

    return note


@garden_note_router.get("/notes/{garden_id}", response_model=list[GardenNoteList])
async def read_garden_notes(
    garden_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:re", "ga:re:own"])
    ],
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> list[GardenNoteList]:
    """
    Route to get a list of GardenNotes

    :param garden_id: The ID of the Garden to retrieve notes
    :param skip: The rows to skip
    :param limit: The number of rows to return
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :return: A list of GardenNote objects; gardens.garden_models.GardenNote
    """

    garden = await GardenCRUD.get_garden(session=session, garden_id=garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope="ga:re"
    )
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope="ga:re:own",
        user_id=current_user.id,
        entity_owner=garden.user_id,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")

    notes = await GardenNoteCRUD.get_notes(
        garden_id=garden_id,
        session=session,
        skip=skip,
        limit=limit,
    )
    return [GardenNoteList.model_validate(note) for note in notes]


@garden_note_router.put("/{note_id}", response_model=GardenNote)
async def update_garden_note(
    note_id: UUID,
    note_update: GardenNoteUpdate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:up", "ga:up:own"])
    ],
    session: AsyncSession = Depends(get_db),
) -> GardenNote:
    """
    Route to update a GardenNote

    :param note_id: The ID of the GardenNote to update
    :param note_update: The GardenNoteUpdate object; gardens.garden_note_schemas.GardenNoteUpdate
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :return: GardenNote; gardens.garden_models.GardenNote
    """

    note = await GardenNoteCRUD.get_note(note_id=note_id, session=session)
    if not note:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope="ga:up"
    )
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope="ga:up:own",
        user_id=current_user.id,
        entity_owner=garden.user_id,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")

    updated_note = await GardenNoteCRUD.update_note(
        session=session,
        note_id=note_id,
        note_update=note_update,
    )
    if updated_note:
        log_handler.log_garden_event(
            event="Note updated",
            context={
                "actor_id": current_user.id,
                "actor_username": current_user.username,
                "garden_id": updated_note.garden_id,
                "note_id": updated_note.id,
                "action": "update_note",
                "resource": "garden_note_routes",
            },
        )
    return updated_note


@garden_note_router.delete("/{note_id}")
async def delete_note(
    note_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["ga:de", "ga:de:own"])
    ],
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    A route to delete a GardenNote

    :param note_id: The ID of the GardenNote to delete
    :param session: SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :return: dict
    """

    note = await GardenNoteCRUD.get_note(session=session, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    garden = await GardenCRUD.get_garden(session=session, garden_id=note.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope="ga:de"
    )
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope="ga:de:own",
        user_id=current_user.id,
        entity_owner=garden.user_id,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")

    log_handler.log_garden_event(
        event="Note deleted",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "garden_id": note.garden_id,
            "note_id": note.id,
            "action": "delete_note",
            "resource": "garden_note_routes",
        },
    )

    return {"message": "Note deleted successfully"}
