import os

from langchain_google_genai import ChatGoogleGenerativeAI

from .base import GenerationOptions
from .langchain_adapter import LangChainProvider


def create_gemini_provider(
    model_name: str | None = None,
) -> LangChainProvider:
    """Create a Gemini provider using the shared LangChain adapter."""

    selected_model = model_name or os.getenv("GEMINI_MODEL")

    if not selected_model:
        raise ValueError("GEMINI_MODEL is not configured")

    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY is not configured")

    def model_factory(options: GenerationOptions):
        kwargs = {
            "model": selected_model,
            "temperature": options.temperature,
            "max_output_tokens": options.max_output_tokens,
            "max_retries": 3,
        }

        if options.response_format == "json":
            kwargs["response_mime_type"] = "application/json"

        return ChatGoogleGenerativeAI(**kwargs)

    return LangChainProvider(
        provider_name="gemini",
        model_name=selected_model,
        model_factory=model_factory,
    )