import time

from .base import (
    BaseModelProvider,
    GenerationOptions,
    ModelResponse,
)


class MockProvider(BaseModelProvider):
    """Development provider that makes no external AI calls."""

    provider_name = "mock"
    model_name = "mock-model"

    def generate(
        self,
        prompt: str,
        *,
        options: GenerationOptions | None = None,
    ) -> ModelResponse:
        start_time = time.perf_counter()

        # Accept the shared interface while retaining the fixed
        # response used to check the benchmark pipeline.
        return ModelResponse(
            text="Mock response generated successfully.",
            latency_ms=(
                time.perf_counter() - start_time
            ) * 1000,
        )