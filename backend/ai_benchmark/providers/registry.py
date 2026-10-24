from .base import BaseModelProvider
from .mock import MockProvider
from .ollama import OllamaProvider


def create_provider(
    provider_name: str,
    *,
    model_name: str | None = None,
    context_length: int | None = None,
    timeout_seconds: float | None = None,
) -> BaseModelProvider:
    if provider_name == "mock":
        if any(
            value is not None
            for value in (
                model_name,
                context_length,
                timeout_seconds,
            )
        ):
            raise ValueError(
                "Model and runtime overrides require Ollama"
            )

        return MockProvider()

    if provider_name == "ollama":
        return OllamaProvider(
            model_name=(
                model_name
                if model_name is not None
                else "qwen3:1.7b"
            ),
            context_length=(
                context_length
                if context_length is not None
                else 4096
            ),
            timeout_seconds=(
                timeout_seconds
                if timeout_seconds is not None
                else 300
            ),
        )

    raise ValueError(
        f"Provider is not implemented: {provider_name}"
    )