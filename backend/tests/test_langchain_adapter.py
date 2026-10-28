
import sys
import unittest
from pathlib import Path

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from ai_benchmark.providers.base import GenerationOptions
from ai_benchmark.providers.langchain_adapter import LangChainProvider

from ai_benchmark.providers.registry import create_provider

class TestLangChainProvider(unittest.TestCase):

    def test_text_response(self):
        model = RunnableLambda(
            lambda prompt: AIMessage(content="Test response")
        )

        provider = LangChainProvider(
            provider_name="test",
            model_name="fake-model",
            model=model,
        )

        response = provider.generate(
            "Hello",
            options=GenerationOptions(
                temperature=0.0,
                max_output_tokens=100,
                response_format="text",
            ),
        )

        self.assertFalse(response.error)
        self.assertEqual(response.text, "Test response")
        self.assertGreaterEqual(response.latency_ms, 0)

    def test_string_response(self):
        model = RunnableLambda(
            lambda prompt: "String response"
        )

        provider = LangChainProvider(
            provider_name="test",
            model_name="fake-model",
            model=model,
        )

        response = provider.generate("Hello")

        self.assertFalse(response.error)
        self.assertEqual(response.text, "String response")

    def test_provider_error(self):
        def failing_model(prompt):
            raise RuntimeError("Simulated provider failure")

        model = RunnableLambda(failing_model)

        provider = LangChainProvider(
            provider_name="test",
            model_name="fake-model",
            model=model,
        )

        response = provider.generate("Hello")

        self.assertTrue(response.error)
        self.assertEqual(response.text, "")
        self.assertIn(
            "Simulated provider failure",
            response.error_message,
        )

    def test_valid_json_response(self):
        model = RunnableLambda(
            lambda prompt: AIMessage(
                content='{"name": "Academic Candidate"}'
            )
        )

        provider = LangChainProvider(
            provider_name="test",
            model_name="fake-model",
            model=model,
        )

        response = provider.generate(
            "Return JSON",
            options=GenerationOptions(
                temperature=0.0,
                max_output_tokens=100,
                response_format="json",
            ),
        )

        self.assertFalse(response.error)
        self.assertEqual(
            response.text,
            '{"name": "Academic Candidate"}',
        )


    def test_invalid_json_response(self):
        invalid_json = '{"name": "Mario"'

        model = RunnableLambda(lambda prompt: AIMessage(content=invalid_json))
        provider = LangChainProvider(
            provider_name="test",
            model_name="fake-model",
            model=model,
        )

        response = provider.generate(
            "Return JSON",
            options=GenerationOptions(response_format="json"),
        )

        self.assertFalse(response.error)
        self.assertEqual(response.text, invalid_json)
        self.assertIsNone(response.error_message)

    def test_model_invoked_once(self):
        calls = []

        def fake_model(prompt):
            calls.append(prompt)
            return AIMessage(content="Single response")

        provider = LangChainProvider(
            provider_name="test",
            model_name="fake-model",
            model=RunnableLambda(fake_model),
        )

        response = provider.generate("Hello")

        self.assertFalse(response.error)
        self.assertEqual(response.text, "Single response")
        self.assertEqual(calls, ["Hello"])

    def test_model_factory_receives_options(self):
        received_options = []

        def factory(settings):
            received_options.append(settings)
            return RunnableLambda(
                lambda prompt: AIMessage(content='{"status": "ok"}')
            )

        provider = LangChainProvider(
            provider_name="test",
            model_name="fake-model",
            model_factory=factory,
        )

        settings = GenerationOptions(
            temperature=0.3,
            max_output_tokens=512,
            response_format="json",
        )

        response = provider.generate("Return JSON", options=settings)

        self.assertFalse(response.error)
        self.assertEqual(len(received_options), 1)
        self.assertEqual(received_options[0], settings)
        self.assertEqual(response.text, '{"status": "ok"}')

    def test_structured_ai_message_extracts_text(self):
        from langchain_core.messages import AIMessage
        from langchain_core.runnables import RunnableLambda

        fake_model = RunnableLambda(
            lambda prompt: AIMessage(
                content=[
                    {
                        "type": "text",
                        "text": "READY",
                        "extras": {"signature": "example"},
                    }
                ]
            )
        )

        provider = LangChainProvider(
            provider_name="langchain",
            model_name="gemini-test",
            model=fake_model,
        )

        result = provider.generate("Reply READY")

        self.assertFalse(result.error)
        self.assertEqual(result.text, "READY")

class TestProviderRegistry(unittest.TestCase):

    def test_create_mock_provider(self):
        provider = create_provider("mock")

        self.assertEqual(provider.provider_name, "mock")

    def test_create_langchain_provider(self):
        model = RunnableLambda(
            lambda prompt: AIMessage(content="Registry works")
        )

        provider = create_provider(
            "langchain",
            model_name="fake-model",
            model=model,
        )

        self.assertIsInstance(provider, LangChainProvider)

        response = provider.generate("Hello")

        self.assertFalse(response.error)
        self.assertEqual(response.text, "Registry works")

    def test_langchain_requires_model_name(self):
        with self.assertRaises(ValueError):
            create_provider("langchain")

    def test_unknown_provider(self):
        with self.assertRaises(ValueError):
            create_provider("unknown")

if __name__ == "__main__":
    unittest.main()
