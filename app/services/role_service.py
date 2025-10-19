import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.logging import get_logger, log_handler
from app.models.role_models import Role
from app.schemas.role_schema import RoleCreate

logger = get_logger(__name__)


class RoleService:

    def __init__(self, session: AsyncSession):
        self._db = session

    async def create_role(self, role: RoleCreate) -> Role:
        """
        Create a new role

        :param role: The RoleCreate object; schemas.role_schema.RoleCreate
        :return: Role object
        """

        db_role = Role(**role.model_dump())

        start = time.time()

        self._db.add(db_role)
        await self._db.commit()
        await self._db.refresh(db_role)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_role",
            table="role",
            duration_ms=duration_ms,
            role_id=str(db_role.id),
        )
        return db_role

    async def get_role(self, role_id: UUID) -> Role | None:
        """
        Get a role

        :param role_id: The role's unique ID
        :return: Role object
        """
        start = time.time()

        role = await self._db.get(Role, role_id)
        rid = str(role.id) if isinstance(role, Role) else "none"

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_role",
            table="role",
            duration_ms=duration_ms,
            role_id=rid,
        )

        return role

    async def get_role_by_name(self, role_name: str) -> Role | None:
        """
        Get a role by the name

        :param role_name: The role name
        :return: The Role or None
        """

        statement = select(Role).where(Role.name == role_name)

        start = time.time()

        result = await self._db.execute(statement)
        role = result.scalars().first()
        rid = str(role.id) if isinstance(role, Role) else "none"

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_role_by_name",
            table="role",
            duration_ms=duration_ms,
            role_id=rid,
        )
        return role

    async def delete_role(self, role_id: UUID) -> bool:
        """
        Delete a role

        :param role_id: The UUID of the role
        :return: bool
        """
        role = await self._db.get(Role, role_id)
        if not isinstance(role, Role):
            return False

        start = time.time()

        await self._db.delete(role)
        await self._db.commit()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="delete_role",
            table="role",
            duration_ms=duration_ms,
            user_id=str(role.id),
        )
        return True
