import json

from benchmark import (
    build_test_cases,
    load_benchmark_configuration,
    render_prompt,
    strip_markdown_json_fence,
)

from providers.base import GenerationOptions
from providers.gemini import create_gemini_provider


def main():
    configuration = load_benchmark_configuration()

    test_config = configuration["test_config"]

    cases = build_test_cases({
        "tests": {
            "test_11_greek_json": test_config["tests"][
                "test_11_greek_json"
            ],
        }
    })

    case = cases[0]
    prompt = render_prompt(case)

    provider = create_gemini_provider()

    options = GenerationOptions(
        temperature=0.0,
        max_output_tokens=8192,
        response_format="json",
    )

    model = provider.model_factory(options)
    response = model.invoke(prompt)

    raw_text = response.text

    print("Model:", provider.model_name)
    print("Case:", case["case_id"])
    print("Response characters:", len(raw_text))

    print("\nResponse metadata:")
    print(response.response_metadata)

    print("\nUsage metadata:")
    print(response.usage_metadata)

    try:
        parsed = json.loads(
            strip_markdown_json_fence(raw_text)
        )
        print("\nJSON valid:", True)
        print("Parsed type:", type(parsed).__name__)

    except json.JSONDecodeError as exc:
        print("\nJSON valid:", False)
        print("JSON error:", exc)
        print("Response ending:", repr(raw_text[-250:]))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Live Gemini JSON diagnostic"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicitly allow a paid or quota-limited API call",
    )
    args = parser.parse_args()

    if not args.live:
        parser.error(
            "This diagnostic makes a live Gemini API request. "
            "Pass --live to run it."
        )

    main()