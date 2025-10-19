from pydantic import BaseModel, ConfigDict


class RoleCreate(BaseModel):
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)
