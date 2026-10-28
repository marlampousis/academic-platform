
from typing import Callable

from langchain_core.runnables import Runnable

from .base import BaseModelProvider, GenerationOptions
from .langchain_adapter import LangChainProvider
from .mock import MockProvider
from .gemini import create_gemini_provider


ModelFactory = Callable[[GenerationOptions], Runnable]


def create_provider(
    provider_name: str,
    *,
    model_name: str | None = None,
    model: Runnable | None = None,
    model_factory: ModelFactory | None = None,
) -> BaseModelProvider:
    """Create a benchmark provider."""

    if provider_name == "mock":
        return MockProvider()

    if provider_name == "langchain":
        if not model_name:
            raise ValueError(
                "model_name is required for LangChain providers"
            )

        return LangChainProvider(
            provider_name=provider_name,
            model_name=model_name,
            model=model,
            model_factory=model_factory,
        )

    if provider_name == "gemini":
        if model is not None or model_factory is not None:
            raise ValueError(
                "Gemini uses its configured model factory"
            )

        return create_gemini_provider(model_name=model_name)

    raise ValueError(
        f"Provider is not implemented: {provider_name}"
    )
