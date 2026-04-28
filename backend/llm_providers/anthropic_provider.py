"""Anthropic provider."""

import logging
from llm_providers.base import LLMClient
from anthropic import Anthropic
logger = logging.getLogger(__name__)

class AnthropicProvider(LLMClient):
    """Anthropic provider."""
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.anthropic.com/v1", max_tokens: int = 1024) -> None:
        """Initialize with Anthropic API key and model name."""
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        self.model = model
        self.max_tokens = max_tokens
        self.client = Anthropic(api_key=api_key, base_url=base_url)
        
    def generate(self, system: str, user: str, temperature: float = 0.7) -> str:
        """Generate text from system and user prompts."""
        message = self.client.messages.create(                              
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}] 
        )
        return message.content[0].text 