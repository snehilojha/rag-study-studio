"""OpenAI provider."""

import logging

from openai import OpenAI
from llm_providers.base import LLMClient
logger = logging.getLogger(__name__)


class OpenAIProvider(LLMClient):
    """LLM provider backed by the OpenAI API (or any OpenAI-compatible endpoint)."""

    def __init__(self, api_key: str, model: str, base_url: str = "", max_tokens: int = 1024) -> None:
        """Initialize with OpenAI API key and model name."""
        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.model = model
        self.max_tokens = max_tokens
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = OpenAI(**client_kwargs)

    def generate(self, system: str, user: str, temperature: float = 0.7) -> str:
        """Send a chat completion request and return the response text."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        logger.debug(
            "OpenAI generate | model=%s | system_len=%d | user_len=%d",
            self.model,
            len(system),
            len(user),
        )

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=messages,
                temperature=temperature,
            )
            choice = response.choices[0]
            content = choice.message.content
            if content is None:
                logger.error(
                    "OpenAI null content | finish_reason=%s | model=%s | usage=%s",
                    choice.finish_reason,
                    response.model,
                    response.usage,
                )
                raise RuntimeError(f"OpenAI returned null content (finish_reason={choice.finish_reason})")
            return content
        except Exception:
            logger.exception("OpenAI chat completion failed")
            raise