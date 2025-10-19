from uuid import UUID

from pydantic import BaseModel


class RoleRequest(BaseModel):
    role_name: str
    user_id: UUID
