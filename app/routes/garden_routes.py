from datetime import datetime, timezone
from typing import List

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.ai.plant_info_agent import get_general_response, get_plant_info
from app.auth import require_role
from app.models.garden import (
    Bed,
    Garden,
    GardenCreate,
    GardenList,
    GardenUpdate,
    Plant,
    PlantCreate,
)
from app.models.users import Role, User

router = APIRouter()


@router.post("/gardens", response_model=Garden)
async def create_garden(
    garden: GardenCreate, user: User = Depends(require_role(Role.ADMIN))
):
    prompt = f"""
    What is the USDA Plant Hardiness Zone for {garden.location}. Respond only with the 2 digit Zone ID
    """
    agent = get_general_response()
    zone = await agent.run(prompt)
    new_garden = Garden(**garden.model_dump(), user=user.id)
    new_garden.zone = zone.output.strip("\n")
    new_garden.beds = [
        Bed(
            name="Default bed",
            description="Edit this bed to add a description",
            plants=None,
        )
    ]
    await new_garden.insert()
    return new_garden


@router.get("/gardens", response_model=List[GardenList])
async def list_gardens():
    gardens = await Garden.find_all().to_list()
    return gardens


@router.get("/gardens/{garden_id}", response_model=Garden)
async def get_garden(garden_id: str):
    garden = await Garden.get(garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    return garden


@router.put("/gardens/{garden_id}", response_model=Garden)
async def put_garden(
    garden_id: PydanticObjectId,
    garden_update: GardenUpdate,
    user: User = Depends(require_role(Role.EDITOR)),
):
    existing_garden = await Garden.get(garden_id)
    if not existing_garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    if existing_user := await existing_garden.user.fetch():
        raise HTTPException(
            status_code=403, detail=f"Permission denied: {existing_user}"
        )

    if not user.id == existing_user.id or user.role.value > Role.EDITOR.value:
        raise HTTPException(status_code=403, detail="Permission denied")

    update_data = garden_update.model_dump(exclude_unset=True)

    if garden_update.location != existing_garden.location:
        prompt = f"""
        What is the USDA Plant Hardiness Zone for {garden_update.location}.
        Respond only with the 2 digit Zone ID
        """
        agent = get_general_response()
        zone = await agent.run(prompt)
        update_data["zone"] = zone.output.strip("\n")

    update_query = {"$set": update_data}
    update_query["$set"]["updated_date"] = datetime.now(timezone.utc)

    await existing_garden.update(update_query)
    return await Garden.get(garden_id)


@router.delete(
    "/gardens/{garden_id}",
)
async def delete_garden(
    garden_id: PydanticObjectId, user: User = Depends(require_role(Role.EDITOR))
):
    existing_garden = await Garden.get(garden_id)
    if not existing_garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    existing_user_id = existing_garden.user.ref.id
    if not user.id == existing_user_id and not user.role.ADMIN:
        raise HTTPException(status_code=403, detail="Permission denied")

    await existing_garden.delete()
    return {"message": "Garden deleted successfully"}


@router.post("/gardens/{garden_id}/plants")
async def add_plant(
    plant: PlantCreate, user: User = Depends((require_role(Role.ADMIN)))
):
    new_plant = Plant(**plant.model_dump())
    search_for: str = (
        f"{plant.variety} {plant.species}" if plant.variety else plant.species
    )
    info_agent = get_plant_info(plant=search_for)
    results = await info_agent.run(f"Tell me about planting a {search_for}")
    new_plant.recommendations = results.output
    await new_plant.insert()
    return new_plant
