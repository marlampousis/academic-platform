from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from math import isfinite
from typing import Any, Literal


@dataclass(frozen=True)
class GenerationOptions:
    """Common generation settings accepted by every provider."""

    temperature: float = 0.0
    max_output_tokens: int = 2048
    response_format: Literal["text", "json"] = "text"

    def __post_init__(self) -> None:
        if (
            type(self.temperature) not in (int, float)
            or not isfinite(self.temperature)
            or not 0.0 <= self.temperature <= 1.0
        ):
            raise ValueError(
                "temperature must be a finite number between 0 and 1"
            )

        if (
            type(self.max_output_tokens) is not int
            or self.max_output_tokens < 1
        ):
            raise ValueError(
                "max_output_tokens must be a positive integer"
            )

        if self.response_format not in ("text", "json"):
            raise ValueError(
                "response_format must be 'text' or 'json'"
            )


@dataclass
class ModelResponse:
    """Standard response returned by every provider."""

    text: str
    latency_ms: float
    error: bool = False
    error_message: str | None = None
    runtime_metadata: dict[str, Any] = field(default_factory=dict)


class BaseModelProvider(ABC):
    """Common interface implemented by all providers."""

    provider_name: str
    model_name: str

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        options: GenerationOptions | None = None,
    ) -> ModelResponse:
        """Generate a response using the supplied options."""
        raise NotImplementedError
