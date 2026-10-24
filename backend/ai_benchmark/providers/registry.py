from .base import BaseModelProvider
from .mock import MockProvider
from .ollama import OllamaProvider


def create_provider(provider_name: str) -> BaseModelProvider:
    if provider_name == "mock":
        return MockProvider()

    if provider_name == "ollama":
        return OllamaProvider()

    raise ValueError(
        f"Provider is not implemented: {provider_name}"
    )