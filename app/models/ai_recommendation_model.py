from enum import Enum

from pydantic import BaseModel


class LifeCycle(str, Enum):
    PERENNIAL = "perennial"
    ANNUAL = "annual"
    BIENNIAL = "biennial"


class PlantingWindow(BaseModel):
    season: str
    months: str | None = None
    temperature_range: str

    class Settings:
        name = "planting_window"


class CareInstructions(BaseModel):
    watering_frequency: str
    sunlight_needs: str
    soil_type: str
    spacing: str | None = None

    class Settings:
        name = "care_instructions"


class GrowingTips(BaseModel):
    tips: str


class Pest(BaseModel):
    pest: str


class AIRecommendations(BaseModel):
    life_cycle: LifeCycle
    days_to_harvest: int | None = None
    companion_plants: str | None = None
    growing_tips: list[GrowingTips]
    planting_window: PlantingWindow
    care_instructions: CareInstructions
    pests: list[Pest] | None = None
