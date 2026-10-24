import time

from .base import BaseModelProvider, ModelResponse


class MockProvider(BaseModelProvider):
    """
    Development provider used to test the benchmark pipeline
    without calling a real language model.
    """

    provider_name = "mock"
    model_name = "mock-model"

    def generate(self, prompt: str) -> ModelResponse:

        start_time = time.perf_counter()

        try:
            response_text = (
                "Mock response generated successfully."
            )

            latency_ms = (
                time.perf_counter() - start_time
            ) * 1000

            return ModelResponse(
                text=response_text,
                latency_ms=latency_ms,
                error=False,
                error_message=None,
            )

        except Exception as exc:

            latency_ms = (
                time.perf_counter() - start_time
            ) * 1000

            return ModelResponse(
                text="",
                latency_ms=latency_ms,
                error=True,
                error_message=str(exc),
            )