"""Base LLM provider contract."""

from abc import ABC, abstractmethod


class LLMClient(ABC):

    @abstractmethod
    def __init__(self, api_key: str, model: str, base_url: str) -> None: ...

    @abstractmethod
    def generate(self, system: str, user: str, temperature: float = 0.7) -> str: ...