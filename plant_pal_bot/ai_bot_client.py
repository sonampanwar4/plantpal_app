from openai import OpenAI, RateLimitError
from settings import Setting
from typing import Optional, Type, Dict, Any, List
import base64
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai.types.chat import (
    ChatCompletionUserMessageParam, ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam
)

from logging import getLogger

logger = getLogger(__name__)

client = OpenAI(api_key=Setting.open_ai_key)

# Function to convert an image to base64
def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def calculate_llm_cost(input_tokens: int, output_tokens: int, llm_model: str = None):
    """
    Calculate total cost (USD) for an OpenAI API request based on token usage.
    Returns:
        float: Total cost in USD.
    """
    # OpenAI pricing per 1M tokens
    PRICING = {
        "gpt-4o-mini": {
            "input": 0.40 / 1_000_000,  # $0.40 per 1M input tokens
            "output": 1.60 / 1_000_000,  # $1.60 per 1M output tokens
        },
        # you can add more models here if needed
        # e.g. "gpt-4o": {"input": 5.00/1e6, "output": 15.00/1e6}
    }

    if llm_model not in PRICING:
        raise ValueError(f"Model '{llm_model}' is not supported in pricing table.")
    total_cost = 0.0
    for model in PRICING:
        if model == llm_model:
            input_rate = PRICING[model]["input"]
            output_rate = PRICING[model]["output"]

            total_cost = (input_tokens * input_rate) + (output_tokens * output_rate)

    print(f"💰 Total cost per request is: {total_cost}")


@retry(
    stop=stop_after_attempt(5),  # Retry up to 3 times
    wait=wait_exponential(multiplier=1, min=10, max=120),
    retry=retry_if_exception_type(RateLimitError),  # Retry on 429 errors
    before_sleep=lambda retry_state: logger.info(
        f"Retrying due to rate limit, attempt {retry_state.attempt_number}, waiting {retry_state.next_action.sleep}s")
)
async def ask_gpt4o(
        user_prompt: str,
        system_prompt: Optional[str] = None,
        image_path: Optional[str] = None,
        response_model: Type[BaseModel] = None,
        token: int = 800, # cheaper & faster
        temperature: float = 0.1 # stable classification
) -> Dict[str, Any]:
    """
    Calls OpenAI and returns a dict validated by `response_model`.

    - Always returns a dict.
    - Never returns None.
    - Throws on API errors or validation errors.
    """
    base_agent_prompt = """You are PlantPal, a friendly and knowledgeable plant care assistant specializing in plant pathology and horticulture.

PRIMARY FUNCTIONS:
- Identify plants and provide species information
- Recommend personalized care (watering, sunlight, soil, fertilizing)
- Diagnose and treat plant diseases and pest damage
- Suggest gardening best practices and plant management strategies

SCOPE - Analyze only plant-related content:
- Indoor/outdoor plants, trees, flowers, shrubs
- Vegetables, fruits, herbs, and their seedlings
- Plant parts: leaves, stems, roots, flowers, bark
- Visible disease, pest damage, or nutrient deficiencies

IMAGE ANALYSIS GUIDELINES:
When analyzing plant images:
1. Provide detailed diagnostic assessment
2. Identify the plant species and condition
3. Reference similar cases to support your diagnosis
4. Consider location, light, and growing conditions in recommendations
5. Offer evidence-based treatment solutions

REJECT INVALID IMAGES - Return an error for:
- People, animals, objects, food, or landscapes without plants
- Screenshots, diagrams, documents, charts, or text
- Corrupted, blurry, or unreadable images
- Abstract/artistic images of non-living subjects

TONE: Friendly, clear, and concise. Use accessible language without oversimplification.

OUTPUT: Always respond strictly in the required JSON format. Do not include text outside the JSON structure."""
    try:
        if system_prompt:
         base_agent_prompt += "\n\n" + system_prompt

        messages = [ChatCompletionUserMessageParam(role="system", content=base_agent_prompt)]
        # If image is provided → encode and attach
        if image_path:
            # Convert image to base64
            b64 = image_to_base64(image_path)
            messages.append(ChatCompletionUserMessageParam(
                role="user",
                content=[
                    ChatCompletionContentPartTextParam(type="text", text=user_prompt),
                    ChatCompletionContentPartImageParam(
                        type="image_url",
                        image_url={"url": f"data:image/jpeg;base64,{b64}"})
                ])
            )
        else:
            # Text-only fallback
            messages.append(ChatCompletionUserMessageParam(role="user", content=user_prompt))

        response = client.beta.chat.completions.parse(
            model=Setting.open_ai_model,
            messages=messages,
            response_format=response_model,
            max_tokens=token,
            temperature=temperature
        )

        # Extract the parsed content (assumes response.choices[0].message.content is the parsed model)
        parsed_content = response.choices[0].message.parsed
        if parsed_content is None:
            raise RuntimeError(f"No parsed content returned from OpenAI API for {response_model}")

        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        # Calculate total cost for a LLM request
        calculate_llm_cost(input_tokens, output_tokens, Setting.open_ai_model)

        return parsed_content.model_dump()
    except RateLimitError as e:
        logger.warning(f"❗ Rate limit error: {str(e)}")
        raise  # Let tenacity handle the retry

    except Exception as e:
        logger.exception("Unexpected error in ask_gpt4o()", e)
        raise


def get_embeddings(texts: List[str]) -> List[List[float]]:
    try:
        response = client.embeddings.create(
            model=Setting.embedding_model,
            input=[t.replace("\n", " ").strip() for t in texts]
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.exception("❌ Failed to generate embedding")
        raise

def get_embedding(text: str) -> List[float]:
    try:
        response = client.embeddings.create(
            model=Setting.embedding_model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.exception("❌ Failed to generate embedding")
        raise