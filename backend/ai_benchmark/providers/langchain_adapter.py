
import json
import time
from typing import Any, Callable

from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable

from .base import BaseModelProvider, GenerationOptions, ModelResponse


ModelFactory = Callable[[GenerationOptions], Runnable]


class LangChainProvider(BaseModelProvider):
    """Adapt a LangChain runnable to the benchmark interface."""

    def __init__(
        self,
        provider_name: str,
        model_name: str,
        model: Runnable | None = None,
        model_factory: ModelFactory | None = None,
    ) -> None:
        if (model is None) == (model_factory is None):
            raise ValueError(
                "Provide exactly one of model or model_factory"
            )

        self.provider_name = provider_name
        self.model_name = model_name
        self.model = model
        self.model_factory = model_factory

    def generate(
        self,
        prompt: str,
        *,
        options: GenerationOptions | None = None,
    ) -> ModelResponse:
        settings = options if options is not None else GenerationOptions()
        start = time.perf_counter()

        try:
            # A factory creates a model with generation settings
            # supported by its specific provider.
            # A plain Runnable is used without model-specific settings.
            if self.model_factory is not None:
                runnable = self.model_factory(settings)
            else:
                runnable = self.model

            response: Any = runnable.invoke(prompt)

            if isinstance(response, AIMessage):
                content = response.content
            elif isinstance(response, str):
                content = response
            else:
                raise TypeError(
                    "Unsupported LangChain response type: "
                    f"{type(response).__name__}"
                )

            if not isinstance(content, str):
                raise TypeError("Expected a text response from the model.")

            if settings.response_format == "json":
                try:
                    json.loads(content)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Model returned invalid JSON: {exc}"
                    ) from exc

            return ModelResponse(
                text=content,
                latency_ms=(time.perf_counter() - start) * 1000,
            )

        except Exception as exc:
            return ModelResponse(
                text="",
                latency_ms=(time.perf_counter() - start) * 1000,
                error=True,
                error_message=f"{type(exc).__name__}: {exc}",
            )
