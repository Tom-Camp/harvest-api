from uuid import UUID

from sqlmodel import SQLModel


class AssignRoleRequest(SQLModel):
    user_id: UUID
    role_name: str


class PermissionCheck(SQLModel):
    resource: str
    action: str
