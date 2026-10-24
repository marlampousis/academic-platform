from .base import BaseModelProvider
from .mock import MockProvider


def create_provider(provider_name: str) -> BaseModelProvider:
    """Create an implemented provider."""

    if provider_name == "mock":
        return MockProvider()

    raise ValueError(
        f"Provider is not implemented: {provider_name}"
    )