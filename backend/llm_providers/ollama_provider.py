"""Ollama provider."""

from llm_providers.openai_provider import OpenAIProvider

class OllamaProvider(OpenAIProvider):
    """LLM provider backed by Ollama (OpenAI-compatible)."""

    def __init__(self,model: str, api_key: str = "ollama", base_url: str = "http://localhost:11434", max_tokens: int = 1024) -> None:
        """Initialize with Ollama and model name."""
        super().__init__(api_key=api_key, model=model, base_url=base_url, max_tokens=max_tokens)    