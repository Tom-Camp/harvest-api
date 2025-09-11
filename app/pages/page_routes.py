from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import AsyncCasbinManager
from app.casbin.permissions import RequirePageRead
from app.logging import get_logger
from app.pages.page_crud import PageCRUD
from app.pages.page_schemas import PageCreate, PageRead, PageUpdate
from app.users.user_models import User
from app.utils.database import get_db
from app.utils.dependencies import get_casbin_manager

logger = get_logger(__name__)

page_router = APIRouter(prefix="/pages")


@page_router.post("/", response_model=PageRead)
async def create_page(
    page: PageCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    logger.info("THIS IS INFO")
    logger.debug("PAGE POST", page)
    return PageCRUD.create_page(session, page, current_user.id)


@page_router.get("/", response_model=List[PageRead])
async def read_pages(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePageRead),
):
    logger.info("%s listed all pages" % current_user.username)
    return PageCRUD.get_pages(session, skip=skip, limit=limit)


@page_router.get("/my", response_model=List[PageRead])
async def read_my_pages(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return PageCRUD.get_user_pages(session, current_user.id, skip=skip, limit=limit)


@page_router.get("/{page_id}", response_model=PageRead)
async def read_page(
    page_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    page = await PageCRUD.get_page(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    allowed = await manager.enforce(
        sub=f"user:{current_user.username}",
        obj="page",
        act="read",
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    return page


@page_router.put("/{page_id}", response_model=PageRead)
async def update_page(
    page_id: UUID,
    page_update: PageUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    page = await PageCRUD.get_page(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    allowed = await manager.enforce(
        sub=f"user:{current_user.username}",
        obj="page",
        act="write",
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    updated_page = PageCRUD.update_page(session, page_id, page_update)
    return updated_page


@page_router.delete("/{page_id}")
async def delete_page(
    page_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    page = await PageCRUD.get_page(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    allowed = await manager.enforce(
        sub=f"user:{current_user.username}",
        obj="page",
        act="write",
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    if not PageCRUD.delete_page(session, page_id):
        raise HTTPException(status_code=404, detail="Page not found")

    return {"message": "Page deleted successfully"}
