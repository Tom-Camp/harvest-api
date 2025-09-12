from uuid import UUID

from pydantic import BaseModel


class RoleRequest(BaseModel):
    user_id: UUID
    username: str
    role_name: str


class PermissionCheck(BaseModel):
    user_id: UUID
    username: str
    resource: str
    action: str
