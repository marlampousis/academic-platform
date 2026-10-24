from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelResponse:
    """
    Standard response returned by every benchmark provider.
    """

    text: str
    latency_ms: float
    error: bool = False
    error_message: Optional[str] = None


class BaseModelProvider(ABC):
    """
    Common interface implemented by all benchmark providers.
    """

    provider_name: str
    model_name: str

    @abstractmethod
    def generate(self, prompt: str) -> ModelResponse:
        """
        Send a prompt to the model and return a standardized response.
        """
        raise NotImplementedError