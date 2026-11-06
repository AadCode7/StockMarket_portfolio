from abc import ABC, abstractmethod
from groq import AsyncGroq
from app.config import settings

class LLMProviderError(RuntimeError):
    pass

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        raise NotImplementedError

class GroqProvider(LLMProvider):
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise LLMProviderError("GROQ_API_KEY is not configured")
        self.client = AsyncGroq(api_key=settings.groq_api_key)

    async def generate(self, prompt: str) -> str:
        try:
            result = await self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content":
                     "You are a research assistant. Never invent prices, metrics, citations, or forecasts. "
                     "State when evidence is missing. This is educational research, not investment advice."},
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            return result.choices[0].message.content or "The model returned an empty response."
        except Exception as exc:
            raise LLMProviderError(f"Groq request failed: {type(exc).__name__}") from exc

def get_llm_provider() -> LLMProvider:
    if settings.llm_provider.lower() != "groq":
        raise LLMProviderError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
    return GroqProvider()
