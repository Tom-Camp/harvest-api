import time

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app.ai.prompts.new_plant import new_plant_prompt
from app.core.utils.config import settings
from app.logging import get_logger, log_handler
from app.models.ai_recommendation_model import AIRecommendations

logger = get_logger(__name__)


model = GoogleModel(
    model_name=settings.GEMINI_MODEL,
    provider=GoogleProvider(api_key=settings.GEMINI_API_KEY),
)


async def get_plant_info(plant: str, location: str) -> AIRecommendations:
    prompt, instructions = new_plant_prompt(plant=plant, location=location)
    plant_agent = Agent(
        model=model,
        output_type=AIRecommendations,
        system_prompt=prompt,
        instructions="\n".join(instructions),
        retries=3,
    )

    start = time.time()
    results = await plant_agent.run(user_prompt=prompt)
    duration_ms = (time.time() - start) * 1000

    if isinstance(results.output, AIRecommendations):
        log_handler.log_ai_operation(
            operation="get_plant_info",
            model=settings.GEMINI_MODEL,
            duration_ms=duration_ms,
            agent="plant_info_agent",
            result="success",
        )
    else:
        log_handler.log_ai_operation(
            operation="get_plant_info",
            model=settings.GEMINI_MODEL,
            duration_ms=duration_ms,
            agent="plant_info_agent",
            result="failure",
            output=results.all_messages(),
        )
    return results.output
