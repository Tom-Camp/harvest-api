import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app.ai.prompts.new_plant import new_plant_prompt
from app.models.garden import PlantInfo

load_dotenv()


def create_model_with_env_token() -> GoogleModel:
    model = GoogleModel(
        model_name=os.getenv("HF_MODEL"),
        provider=GoogleProvider(api_key=os.getenv("HF_TOKEN")),
    )
    return model


def get_plant_info(plant: str) -> Agent:
    prompt, instructions = new_plant_prompt(plant)
    plant_agent = Agent(
        model=create_model_with_env_token(),
        output_type=PlantInfo,
        system_prompt=prompt,
        instructions="\n".join(instructions),
        retries=3,
    )
    return plant_agent


def get_general_response() -> Agent:
    zone_agent = Agent(model=create_model_with_env_token(), retries=3)
    return zone_agent
