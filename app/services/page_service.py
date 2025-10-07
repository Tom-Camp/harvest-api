import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.logging import get_logger, log_handler
from app.models.page_models import Page
from app.schemas.page_schemas import PageCreate, PageUpdate

logger = get_logger(__name__)


class PageService:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def create_page(self, page: PageCreate, user_id: UUID) -> Page:
        """
        Create a new page

        :param page: The PageCreate object; pages.page_schemas.PageCreate
        :param user_id: The UUID of the user
        :return: Page
        """

        db_page = Page(**page.model_dump(), user_id=user_id)

        start = time.time()

        self._db.add(db_page)
        await self._db.commit()
        await self._db.refresh(db_page)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_page",
            table="page",
            duration_ms=duration_ms,
            page_id=str(db_page.id),
        )
        return db_page

    async def get_page(self, page_id: UUID) -> Page | None:
        """
        Get a page by ID

        :param page_id: The unique ID of the page
        :return: a Page object or None
        """
        return await self._db.get(Page, page_id)

    async def get_pages(self, skip: int = 0, limit: int = 100) -> Sequence[Page]:
        """
        Get all pages

        :param skip: The number of pages to skip
        :param limit: The number of pages to return
        :return: Sequence[Page]
        """
        statement = select(Page).offset(skip).limit(limit)

        start = time.time()

        result = await self._db.execute(statement)
        pages = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_pages",
            table="page",
            duration_ms=duration_ms,
            list_length=len(pages),
        )
        return pages

    async def get_user_pages(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Page]:
        """
        Get all user's pages

        :param user_id: The UUID of the user
        :param skip: The number of pages to skip
        :param limit: The number of pages to return
        :return: Sequence[Page]
        """

        statement = (
            select(Page).where(Page.user_id == user_id).offset(skip).limit(limit)
        )
        start = time.time()

        result = await self._db.execute(statement)
        pages = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_user_pages",
            table="page",
            duration_ms=duration_ms,
            list_length=len(pages),
        )
        return pages

    async def update_page(self, page_id: UUID, page_update: PageUpdate) -> Page | None:
        """
        Update a page by ID

        :param page_id: The UUID of the page
        :param page_update: The PageUpdate object
        :return: Page or None
        """

        page: Page | None = await self._db.get(Page, page_id)
        if page:
            page_data = page_update.model_dump(exclude_unset=True)
            for field, value in page_data.items():
                setattr(page, field, value)

            start = time.time()

            self._db.add(page)
            await self._db.commit()
            await self._db.refresh(page)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_page",
                table="page",
                duration_ms=duration_ms,
                page_id=str(page_id),
            )
        return page

    async def delete_page(self, page_id: UUID) -> bool:
        """
        Delete a page by ID

        :param page_id: The UUID of the page
        :return: bool
        """
        page = await self._db.get(Page, page_id)
        if page:
            start = time.time()

            await self._db.delete(page)
            await self._db.commit()

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_page",
                table="page",
                duration_ms=duration_ms,
                page_id=str(page_id),
            )
            return True
        return False
