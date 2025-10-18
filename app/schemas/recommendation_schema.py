from pydantic import BaseModel, ConfigDict


class CareInstructionsRead(BaseModel):
    watering_frequency: str
    sunlight_needs: str
    soil_type: str
    spacing: str | None

    model_config = ConfigDict(from_attributes=True)


class GrowingTipsRead(BaseModel):
    tips: str

    model_config = ConfigDict(from_attributes=True)


class PestRead(BaseModel):
    pest: str

    model_config = ConfigDict(from_attributes=True)


class PlantingWindowRead(BaseModel):
    season: str
    months: str | None = None
    temperature_range: str

    model_config = ConfigDict(from_attributes=True)


class RecommendationRead(BaseModel):
    life_cycle: str
    days_to_harvest: int | None = None
    companion_plants: str | None = None
    planting_window: PlantingWindowRead
    care_instructions: CareInstructionsRead
    pests: list[PestRead] | None = None
