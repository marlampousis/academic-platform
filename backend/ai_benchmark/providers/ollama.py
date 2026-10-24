import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import (
    BaseModelProvider,
    GenerationOptions,
    ModelResponse,
)


class OllamaProvider(BaseModelProvider):
    """Local Ollama provider using the HTTP generation API."""

    provider_name = "ollama"

    def __init__(
        self,
        model_name: str = "qwen3:1.7b",
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: float = 300,
        context_length: int = 4096,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.context_length = context_length

    def generate(
        self,
        prompt: str,
        *,
        options: GenerationOptions | None = None,
    ) -> ModelResponse:
        options = options or GenerationOptions()
        started = time.perf_counter()

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": options.temperature,
                "num_predict": options.max_output_tokens,
                "num_ctx": self.context_length,
            },
        }

        if options.response_format == "json":
            payload["format"] = "json"

        request = Request(
            url=f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                data = json.loads(
                    response.read().decode("utf-8")
                )

        except HTTPError as exc:
            return self._failure(
                started,
                f"Ollama returned HTTP {exc.code}",
            )

        except (URLError, TimeoutError, OSError) as exc:
            return self._failure(
                started,
                f"Ollama connection or timeout failure "
                f"({type(exc).__name__})",
            )

        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._failure(
                started,
                "Ollama returned an invalid HTTP response body",
            )

        if not isinstance(data, dict):
            return self._failure(
                started,
                "Ollama response must be an object",
            )

        if data.get("error"):
            return self._failure(
                started,
                "Ollama reported a generation error",
            )

        if data.get("done") is not True:
            return self._failure(
                started,
                "Ollama did not complete the response",
            )

        text = data.get("response")

        if not isinstance(text, str) or not text.strip():
            return self._failure(
                started,
                "Ollama returned an empty or invalid answer",
            )

        return ModelResponse(
            text=text,
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    @staticmethod
    def _failure(
        started: float,
        message: str,
    ) -> ModelResponse:
        return ModelResponse(
            text="",
            latency_ms=(time.perf_counter() - started) * 1000,
            error=True,
            error_message=message,
        )