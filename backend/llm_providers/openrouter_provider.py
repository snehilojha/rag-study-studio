"""OpenRouter provider — OpenAI-compatible endpoint."""

from llm_providers.openai_provider import OpenAIProvider


class OpenRouterProvider(OpenAIProvider):
    """LLM provider backed by OpenRouter (OpenAI-compatible)."""

    def __init__(self, api_key: str, model: str, base_url: str = "https://openrouter.ai/api/v1", max_tokens: int = 1024) -> None:
        """Initialize with OpenRouter API key and model name."""
        super().__init__(api_key=api_key, model=model, base_url=base_url, max_tokens=max_tokens)