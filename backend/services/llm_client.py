"""
LLM client orchestration.
Reads provider from env var, selects appropriate Provider implementation.
"""
import logging
from llm_providers.base import LLMClient
from llm_providers.anthropic_provider import AnthropicProvider
from llm_providers.openai_provider import OpenAIProvider
from llm_providers.openrouter_provider import OpenRouterProvider
from llm_providers.ollama_provider import OllamaProvider
from config import settings
from functools import lru_cache

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """Factory for LLM client. Selects provider from env var."""
    provider = settings.LLM_PROVIDER
    logger.info("LLM provider: %s", provider)
    if provider == "anthropic":
        return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY, model=settings.LLM_MODEL)
    elif provider == "openai":
        return OpenAIProvider(api_key=settings.OPENAI_API_KEY, model=settings.LLM_MODEL)
    elif provider == "openrouter":
        return OpenRouterProvider(api_key=settings.OPENROUTER_API_KEY, model=settings.LLM_MODEL, base_url=settings.OPENROUTER_BASE_URL)
    elif provider == "ollama":
        return OllamaProvider(model=settings.LLM_MODEL, base_url=settings.OLLAMA_BASE_URL)
    else:   
        raise ValueError(f"Unknown LLM provider: {provider}")   
