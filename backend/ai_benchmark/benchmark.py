import os
import json
import time
from pathlib import Path
from typing import Any
import hashlib
import re
from dataclasses import asdict
import argparse

from providers.base import BaseModelProvider, ModelResponse, GenerationOptions
from providers.mock import MockProvider
from providers.registry import create_provider
from benchmark_logging import logger

from evaluators.automatic import (
    evaluate_basic_automatic_metrics,
)

from evaluators.test_01 import evaluate_test_01, validate_test_01_expected_data

from evaluators.test_02 import evaluate_test_02
from evaluators.test_03 import evaluate_test_03
from evaluators.test_04 import evaluate_test_04
from evaluators.test_05 import evaluate_test_05
from evaluators.test_06 import evaluate_test_06
from evaluators.test_07 import evaluate_test_07
from evaluators.test_08 import evaluate_test_08
from evaluators.test_09 import evaluate_test_09
from evaluators.test_10 import evaluate_test_10
from evaluators.test_11 import evaluate_test_11
from evaluators.test_12 import evaluate_test_12

from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_DIR = BASE_DIR / "dataset"
PROMPTS_DIR = BASE_DIR / "prompts"
EXPECTED_DIR = BASE_DIR / "expected"
EVALUATION_DIR = BASE_DIR / "evaluation"
RESULTS_DIR = BASE_DIR / "results"

RUBRIC_FILE = EVALUATION_DIR / "rubric.json"
TEST_CONFIG_FILE = EVALUATION_DIR / "test_config.json"
RESULT_SCHEMA_FILE = EVALUATION_DIR / "result_schema.json"


# ============================================================
# GENERIC FILE LOADERS
# ============================================================

def load_json(path: Path) -> dict[str, Any]:
    """
    Load and return a JSON file.
    """

    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_text(path: Path) -> str:
    """
    Load and return a UTF-8 text file.
    """

    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")

    return path.read_text(encoding="utf-8")

def json_to_prompt_text(data: dict[str, Any]) -> str:
    """
    Convert JSON data to readable UTF-8 text for inclusion
    in a model prompt.
    """

    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )


# ============================================================
# BENCHMARK CONFIGURATION
# ============================================================

def load_benchmark_configuration() -> dict[str, Any]:
    """
    Load the common benchmark configuration files.
    """

    return {
        "rubric": load_json(RUBRIC_FILE),
        "test_config": load_json(TEST_CONFIG_FILE),
        "result_schema": load_json(RESULT_SCHEMA_FILE),
    }


# ============================================================
# TEST FILE DISCOVERY
# ============================================================

def get_prompt_file(test_id: str) -> Path:
    """
    Find the prompt file that corresponds to a test ID.
    """

    matches = list(PROMPTS_DIR.glob(f"{test_id}.txt"))

    if not matches:
        raise FileNotFoundError(
            f"No prompt file found for test: {test_id}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple prompt files found for test: {test_id}"
        )

    return matches[0]


def get_expected_file(test_id: str) -> Path:
    """
    Find the expected-result file that corresponds to a test ID.

    Example:
        test_01_extraction
        -> test_01_expected.json
    """

    test_number = test_id.split("_")[1]

    matches = list(
        EXPECTED_DIR.glob(f"test_{test_number}_expected.json")
    )

    if not matches:
        raise FileNotFoundError(
            f"No expected file found for test: {test_id}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple expected files found for test: {test_id}"
        )

    return matches[0]


# ============================================================
# DATASET DISCOVERY
# ============================================================

def get_candidate_file(case_id: str) -> Path:
    """
    Return the dataset file corresponding to a candidate case.
    """

    candidate_file = DATASET_DIR / f"{case_id}.json"

    if not candidate_file.exists():
        raise FileNotFoundError(
            f"Candidate dataset not found: {candidate_file}"
        )

    return candidate_file


def test_requires_position(test_id: str) -> bool:
    """
    Return True when the benchmark test requires Position A context.
    """

    position_tests = {
        "test_03_alignment",
        "test_04_explainable_alignment",
        "test_08_evidence_retrieval",
        "test_09_potential_gaps",
    }

    return test_id in position_tests


def get_position_file(case_id: str) -> Path:
    """
    Return the appropriate English or Greek position dataset.
    """

    if case_id.endswith("_gr"):
        position_file = DATASET_DIR / "position_a_gr.json"
    else:
        position_file = DATASET_DIR / "position_a.json"

    if not position_file.exists():
        raise FileNotFoundError(
            f"Position dataset not found: {position_file}"
        )

    return position_file


# ============================================================
# CASE CONSTRUCTION
# ============================================================

def build_test_cases(
    test_config: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Convert test_config.json into individual benchmark cases.
    """

    benchmark_cases = []

    tests = test_config["tests"]

    for test_id, config in tests.items():

        prompt_file = get_prompt_file(test_id)
        expected_file = get_expected_file(test_id)

        for case_id in config["cases"]:

            dataset_files = [
                get_candidate_file(case_id)
            ]

            if test_requires_position(test_id):
                dataset_files.append(
                    get_position_file(case_id)
                )

            benchmark_cases.append(
                {
                    "test_id": test_id,
                    "case_id": case_id,
                    "prompt_file": prompt_file,
                    "expected_file": expected_file,
                    "dataset_files": dataset_files,
                    "automatic_metrics": config.get(
                        "automatic_metrics", []
                    ),
                    "qualitative_metrics": config.get(
                        "qualitative_metrics", []
                    ),
                    "safety_metrics": config.get(
                        "safety_metrics", []
                    ),
                }
            )

    return benchmark_cases

# ============================================================
# PROMPT RENDERING
# ============================================================


def render_prompt(
    benchmark_case: dict[str, Any]
) -> str:
    """
    Render a benchmark prompt with candidate and position
    data, without exposing expected evaluation results.
    """

    prompt = load_text(
        benchmark_case["prompt_file"]
    ).strip()

    dataset_files = benchmark_case["dataset_files"]

    candidate_data = load_json(dataset_files[0])
    candidate_text = json_to_prompt_text(candidate_data)

    if "{{candidate}}" in prompt:
        prompt = prompt.replace(
            "{{candidate}}",
            candidate_text
        )
    else:
        prompt += (
            "\n\n=== CANDIDATE CONTEXT ===\n"
            + candidate_text
        )

    position_files = [
        path
        for path in dataset_files[1:]
        if path.stem.startswith("position_")
    ]

    if "{{position}}" in prompt:
        if len(position_files) != 1:
            raise ValueError(
                "Prompt requires exactly one position dataset."
            )

        position_data = load_json(position_files[0])

        prompt = prompt.replace(
            "{{position}}",
            json_to_prompt_text(position_data)
        )

    elif position_files:
        position_data = load_json(position_files[0])

        prompt += (
            "\n\n=== POSITION CONTEXT ===\n"
            + json_to_prompt_text(position_data)
        )

    return prompt


# ============================================================
# RUN SPECIFICATION GENERATION
# ============================================================

def build_run_specifications(
    benchmark_cases: list[dict[str, Any]],
    runs_per_test_case: int,
) -> list[dict[str, Any]]:
    """
    Expand benchmark cases into repeated benchmark runs.
    """

    run_specifications = []

    for case in benchmark_cases:

        rendered_prompt = render_prompt(case)

        for run_number in range(
            1,
            runs_per_test_case + 1
        ):

            run_specifications.append(
                {
                    "test_id": case["test_id"],
                    "case_id": case["case_id"],
                    "run_number": run_number,
                    "prompt_file": case["prompt_file"],
                    "expected_file": case["expected_file"],
                    "dataset_files": case["dataset_files"],
                    "rendered_prompt": rendered_prompt,
                    "automatic_metrics": case[
                        "automatic_metrics"
                    ],
                    "qualitative_metrics": case[
                        "qualitative_metrics"
                    ],
                    "safety_metrics": case[
                        "safety_metrics"
                    ],
                }
            )

    return run_specifications


def validate_run_specifications(
    run_specifications: list[dict[str, Any]],
    expected_count: int,
) -> None:
    """
    Validate generated benchmark run specifications.
    """

    if len(run_specifications) != expected_count:
        raise ValueError(
            "Unexpected number of run specifications. "
            f"Expected {expected_count}, "
            f"got {len(run_specifications)}."
        )

    seen_runs = set()

    for run in run_specifications:

        key = (
            run["test_id"],
            run["case_id"],
            run["run_number"],
        )

        if key in seen_runs:
            raise ValueError(
                f"Duplicate run specification: {key}"
            )

        seen_runs.add(key)

        if not run["rendered_prompt"].strip():
            raise ValueError(
                f"Empty rendered prompt for: {key}"
            )


def print_run_summary(
    run_specifications: list[dict[str, Any]]
) -> None:
    """
    Print summary information for generated runs.
    """

    print()
    print("=" * 60)
    print("BENCHMARK RUN SPECIFICATIONS")
    print("=" * 60)

    print(
        f"Total generated runs: "
        f"{len(run_specifications)}"
    )

    if run_specifications:

        first_run = run_specifications[0]
        last_run = run_specifications[-1]

        print()
        print(
            "First run: "
            f"{first_run['test_id']} | "
            f"{first_run['case_id']} | "
            f"run {first_run['run_number']}"
        )

        print(
            "Last run: "
            f"{last_run['test_id']} | "
            f"{last_run['case_id']} | "
            f"run {last_run['run_number']}"
        )

    print("=" * 60)
    
# ============================================================
# EXPECTED DATA RESOLUTION
# ============================================================


def resolve_expected_data(
    expected_file: Path,
    case_id: str,
) -> dict[str, Any]:
    """
    Load the expected-result file and return the expected
    ground-truth data for the current benchmark case.

    Supports:
    1. Multi-case expected files.
    2. Single-case expected files.
    3. Expected data nested under 'expected'.
    """

    expected_file_data = load_json(
        expected_file
    )

    cases = expected_file_data.get("cases")

    # Multi-case expected file
    if isinstance(cases, list):

        for case in cases:

            if case.get("candidate") == case_id:

                expected = case.get(
                    "expected"
                )

                if isinstance(
                    expected,
                    dict,
                ):
                    return expected

                # Special handling for Test 09
                if expected_file_data.get("test_id") == "test_09_potential_gaps":
                    return {
                        **case,
                        "expected_schema": expected_file_data["expected_schema"],
                    }

                return case

        raise ValueError(
            "No expected case found for "
            f"case_id={case_id} in "
            f"{expected_file.name}"
        )

    # Single-case expected file
    # Test 11 requires the complete expected-data structure.
    if expected_file_data.get("test_id") == "test_11_greek_json":
        return expected_file_data

    expected = expected_file_data.get("expected")

    if isinstance(expected, dict):
        return expected

    return expected_file_data


# ============================================================
# AUTOMATIC EVALUATION
# ============================================================

def evaluate_automatic_metrics(
    run_specification: dict[str, Any],
    raw_response: str,
    parsed_response: Any,
    json_validity: bool | None,
    expected_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate generic and test-specific automatic metrics.
    """

    metrics = evaluate_basic_automatic_metrics(
        test_id=run_specification[
            "test_id"
        ],
        raw_response=raw_response,
        parsed_response=parsed_response,
        json_validity=json_validity,
        expected_data=expected_data,
        requested_metrics=run_specification[
            "automatic_metrics"
        ],
    )

    test_id = run_specification[
        "test_id"
    ]

    if test_id == "test_01_extraction":

        validate_test_01_expected_data(
            expected_data
        )

        test_specific_metrics = (
            evaluate_test_01(
                parsed_response,
                expected_data,
            )
        )

        metrics.update(
            test_specific_metrics
        )
        
    elif test_id == "test_02_summary":

        test_specific_metrics = evaluate_test_02(
            raw_response=raw_response,
            expected_data=expected_data,
        )

        metrics.update(test_specific_metrics)    

    
    elif test_id == "test_03_alignment":

        test_specific_metrics = evaluate_test_03(
            raw_response=raw_response,
            expected_data=expected_data,
        )

        metrics.update(test_specific_metrics)
        
    
    elif test_id == "test_04_explainable_alignment":

        test_specific_metrics = evaluate_test_04(
            parsed_response=parsed_response,
            expected_data=expected_data,
        )

        metrics.update(test_specific_metrics)    

    elif test_id == "test_05_grounded_qa":

        test_specific_metrics = evaluate_test_05(
            raw_response=raw_response,
            expected_data=expected_data,
        )

        metrics.update(test_specific_metrics)
    
    elif test_id == "test_06_missing_thesis":

        test_specific_metrics = evaluate_test_06(
            raw_response=raw_response,
            expected_data=expected_data,
        )

        metrics.update(test_specific_metrics)
    
    elif test_id == "test_07_missing_hindex":

        test_specific_metrics = evaluate_test_07(
            raw_response=raw_response,
            expected_data=expected_data,
        )

        metrics.update(test_specific_metrics)
    
    elif test_id == "test_08_evidence_retrieval":
        test_specific_metrics = evaluate_test_08(
            parsed_response=parsed_response,
            expected_data=expected_data,
        )
        metrics.update(test_specific_metrics)
        
    elif test_id == "test_09_potential_gaps":
        test_specific_metrics = evaluate_test_09(
            parsed_response=parsed_response,
            expected_data=expected_data,
            expected_schema=expected_data["expected_schema"],
        )

        metrics.update(test_specific_metrics)
    
    elif test_id == "test_10_greek_qa":
        test_specific_metrics = evaluate_test_10(
            raw_response=raw_response,
            expected_data=expected_data,
        )
        metrics.update(test_specific_metrics)
                        
    elif test_id == "test_11_greek_json":
        test_specific_metrics = evaluate_test_11(
            parsed_response=parsed_response,
            expected_data=expected_data,
        )
        metrics.update(test_specific_metrics)
            

    elif test_id == "test_12_adversarial_grounding":
        test_specific_metrics = evaluate_test_12(
            parsed_response=parsed_response,
            expected_data=expected_data,
        )
        metrics.update(test_specific_metrics)

    return metrics
    
# ============================================================
# MODEL EXECUTION
# ============================================================

def execute_run(
    run_specification: dict[str, Any],
    provider: BaseModelProvider,
) -> dict[str, Any]:
    """
    Execute one benchmark run, parse the response,
    and calculate basic automatic metrics.
    """

    logger.info(
        "run_started test=%s case=%s run=%s provider=%s model=%s",
        run_specification["test_id"],
        run_specification["case_id"],
        run_specification["run_number"],
        provider.provider_name,
        provider.model_name,
    )

    options = GenerationOptions(
        temperature=0.0,
        max_output_tokens=8192,
        response_format=(
            "json"
            if expects_json_response(run_specification["test_id"])
            else "text"
        ),
    )

    started_at = datetime.now(timezone.utc).isoformat()

    try:
        response: ModelResponse = provider.generate(
            run_specification["rendered_prompt"],
            options=options,
        )
    except Exception as exc:
        logger.error(
            "run_unexpected_failure test=%s case=%s run=%s provider=%s model=%s exception_type=%s",
            run_specification["test_id"],
            run_specification["case_id"],
            run_specification["run_number"],
            provider.provider_name,
            provider.model_name,
            type(exc).__name__,
        )
        raise

    logger.log(
        30 if response.error else 20,
        "run_finished test=%s case=%s run=%s provider=%s model=%s latency_ms=%.2f error=%s",
        run_specification["test_id"],
        run_specification["case_id"],
        run_specification["run_number"],
        provider.provider_name,
        provider.model_name,
        response.latency_ms,
        response.error,
    )

    expected_data = resolve_expected_data(
        expected_file=run_specification["expected_file"],
        case_id=run_specification["case_id"],
    )

    if response.error:
        # No completed answer is available for quality evaluation.
        parsing_result = {
            "parsed_response": None,
            "json_validity": None,
            "parse_error": None,
        }
        automatic_metrics = {}

    else:
        parsing_result = parse_model_response(
            test_id=run_specification["test_id"],
            raw_response=response.text,
        )

        automatic_metrics = evaluate_automatic_metrics(
            run_specification=run_specification,
            raw_response=response.text,
            parsed_response=parsing_result["parsed_response"],
            json_validity=parsing_result["json_validity"],
            expected_data=expected_data,
        )

    return {
        "timestamp": started_at,
        "requested_generation_options": asdict(options),
        "test_id": run_specification["test_id"],
        "case_id": run_specification["case_id"],
        "run_number": run_specification["run_number"],
        "provider": provider.provider_name,
        "model": provider.model_name,

        "raw_response": response.text,
        "parsed_response": parsing_result["parsed_response"],
        "json_validity": parsing_result["json_validity"],
        "parse_error": parsing_result["parse_error"],

        "latency_ms": response.latency_ms,
        "error": response.error,
        "error_message": response.error_message,

        "automatic_metrics": automatic_metrics,

        "qualitative_metrics": {
            metric: None
            for metric in run_specification["qualitative_metrics"]
        },

        "safety_metrics": {
            metric: None
            for metric in run_specification["safety_metrics"]
        },
    }


# ============================================================
# RESPONSE PARSING
# ============================================================

JSON_RESPONSE_TESTS = {
    "test_01_extraction",
    "test_04_explainable_alignment",
    "test_09_potential_gaps",
    "test_08_evidence_retrieval",
    "test_11_greek_json",
    "test_12_adversarial_grounding",
}


def expects_json_response(test_id: str) -> bool:
    """
    Return True when the benchmark test requires JSON output.
    """

    return test_id in JSON_RESPONSE_TESTS


def strip_markdown_json_fence(text: str) -> str:
    """
    Remove a surrounding Markdown JSON/code fence when present.

    The raw model response is never modified. This function is
    used only for the parsed representation.
    """

    stripped = text.strip()

    if stripped.startswith("```json"):
        stripped = stripped[len("```json"):]

        if stripped.endswith("```"):
            stripped = stripped[:-3]

    elif stripped.startswith("```"):
        stripped = stripped[3:]

        if stripped.endswith("```"):
            stripped = stripped[:-3]

    return stripped.strip()


def parse_model_response(
    test_id: str,
    raw_response: str,
) -> dict[str, Any]:
    """
    Parse a raw model response according to the expected
    response type of the benchmark test.
    """

    if not expects_json_response(test_id):
        return {
            "parsed_response": raw_response.strip(),
            "json_validity": None,
            "parse_error": None,
        }

    cleaned_response = strip_markdown_json_fence(
        raw_response
    )

    try:
        parsed = json.loads(cleaned_response)

        return {
            "parsed_response": parsed,
            "json_validity": True,
            "parse_error": None,
        }

    except json.JSONDecodeError as exc:

        return {
            "parsed_response": None,
            "json_validity": False,
            "parse_error": str(exc),
        }

# ============================================================
# BENCHMARK VALIDATION
# ============================================================

def validate_benchmark_cases(
    benchmark_cases: list[dict[str, Any]]
) -> None:
    """
    Perform basic structural validation of all benchmark cases.
    """

    if not benchmark_cases:
        raise ValueError("No benchmark cases were generated.")

    seen_pairs = set()

    for case in benchmark_cases:

        key = (
            case["test_id"],
            case["case_id"],
        )

        if key in seen_pairs:
            raise ValueError(
                f"Duplicate benchmark case detected: {key}"
            )

        seen_pairs.add(key)

        if not case["prompt_file"].exists():
            raise FileNotFoundError(
                case["prompt_file"]
            )

        if not case["expected_file"].exists():
            raise FileNotFoundError(
                case["expected_file"]
            )

        for dataset_file in case["dataset_files"]:
            if not dataset_file.exists():
                raise FileNotFoundError(
                    dataset_file
                )


# ============================================================
# BENCHMARK SUMMARY
# ============================================================

def print_benchmark_summary(
    benchmark_cases: list[dict[str, Any]],
    runs_per_test_case: int,
) -> None:
    """
    Print a summary of the benchmark configuration.
    """

    print()
    print("=" * 60)
    print("AI BENCHMARK CONFIGURATION")
    print("=" * 60)

    print(f"Test cases: {len(benchmark_cases)}")
    print(f"Runs per test case: {runs_per_test_case}")

    total_runs = (
        len(benchmark_cases)
        * runs_per_test_case
    )

    print(f"Runs per model/provider: {total_runs}")

    print()
    print("Cases:")

    for case in benchmark_cases:
        datasets = ", ".join(
            file.name
            for file in case["dataset_files"]
        )

        print(
            f"  {case['test_id']} "
            f"| {case['case_id']} "
            f"| {datasets}"
        )

    print("=" * 60)



# ============================================================
# RESULT SERIALIZATION AND VALIDATION
# ============================================================

def build_result_record(
    run_specification: dict[str, Any],
    result: dict[str, Any],
    batch_id: str,
) -> dict[str, Any]:
    """Build a complete result record for one run."""

    return {
        "run_id": str(uuid4()),
        "batch_id": batch_id,
        "timestamp": result["timestamp"],
        "requested_generation_options": result[
            "requested_generation_options"
        ],
        "provider": result["provider"],
        "model": result["model"],
        "test_id": result["test_id"],
        "case_id": result["case_id"],
        "run_number": result["run_number"],
        "input": {
            "prompt_file": str(
                run_specification["prompt_file"]
            ),
            "dataset_files": [
                str(path)
                for path in run_specification["dataset_files"]
            ],
            "expected_file": str(
                run_specification["expected_file"]
            ),
            "rendered_prompt": run_specification[
                "rendered_prompt"
            ],
        },
        "output": {
            "raw_response": result["raw_response"],
            "parsed_response": result["parsed_response"],
            "json_validity": result["json_validity"],
            "parse_error": result["parse_error"],
        },
        "execution": {
            "latency_ms": result["latency_ms"],
            "error": result["error"],
            "error_message": result["error_message"],
        },
        "evaluation": {
            "automatic_metrics": result[
                "automatic_metrics"
            ],
            "qualitative_metrics": result[
                "qualitative_metrics"
            ],
            "safety_metrics": result[
                "safety_metrics"
            ],
        },
    }


def validate_result_record(
    record: dict[str, Any],
    result_schema: dict[str, Any],
    rubric: dict[str, Any],
    run_specification: dict[str, Any],
) -> None:
    """Validate result structure and evaluation values."""

    definitions = result_schema["field_definitions"]

    batch_id = record.get("batch_id")
    if not isinstance(batch_id, str):
        raise ValueError("batch_id must be a UUID string")

    try:
        __import__("uuid").UUID(batch_id)
    except ValueError as exc:
        raise ValueError("Invalid batch_id UUID") from exc

    requested_options = record.get("requested_generation_options")
    if not isinstance(requested_options, dict):
        raise ValueError("Invalid requested_generation_options")

    option_keys = {
        "temperature",
        "max_output_tokens",
        "response_format",
    }
    if set(requested_options) != option_keys:
        raise ValueError("Generation option keys mismatch")

    validated_options = GenerationOptions(**requested_options)

    expected_format = (
        "json"
        if expects_json_response(run_specification["test_id"])
        else "text"
    )
    if validated_options.response_format != expected_format:
        raise ValueError("Response format does not match the test")

    def check_object(
        obj: Any,
        required: list[str],
        label: str,
    ) -> None:
        if not isinstance(obj, dict):
            raise ValueError(f"{label} must be an object")

        missing = set(required) - set(obj)
        if missing:
            raise ValueError(
                f"{label} missing fields: {sorted(missing)}"
            )

    check_object(
        record,
        result_schema["required_fields"],
        "result",
    )

    for field in (
        "run_id", "timestamp", "provider", "model",
        "test_id", "case_id",
    ):
        if not isinstance(record[field], str) or not record[field]:
            raise ValueError(f"Invalid {field}")

    try:
        uuid4_value = __import__("uuid").UUID(record["run_id"])
    except (ValueError, AttributeError) as exc:
        raise ValueError("Invalid run_id UUID") from exc

    try:
        timestamp = datetime.fromisoformat(
            record["timestamp"].replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError("Invalid timestamp") from exc

    if timestamp.utcoffset() is None or timestamp.utcoffset().total_seconds() != 0:
        raise ValueError("Timestamp must be UTC")

    allowed = definitions["provider"]["allowed_values"]
    if record["provider"] not in allowed:
        raise ValueError("Unknown provider")

    if (
        type(record["run_number"]) is not int
        or record["run_number"] < 1
    ):
        raise ValueError("Invalid run_number")

    for field in ("test_id", "case_id", "run_number"):
        if record[field] != run_specification[field]:
            raise ValueError(f"Mismatched {field}")

    for section in ("input", "output", "execution", "evaluation"):
        check_object(
            record[section],
            definitions[section]["required_fields"],
            section,
        )

    input_data = record["input"]
    if not all(
        isinstance(input_data[field], str)
        for field in (
            "prompt_file",
            "expected_file",
            "rendered_prompt",
        )
    ):
        raise ValueError("Invalid input text fields")

    if (
        not isinstance(input_data["dataset_files"], list)
        or not all(
            isinstance(item, str)
            for item in input_data["dataset_files"]
        )
    ):
        raise ValueError("Invalid dataset_files")

    output = record["output"]

    json_validity = output.get("json_validity")
    parse_error = output.get("parse_error")

    if json_validity is not None and type(json_validity) is not bool:
        raise ValueError("Invalid json_validity")

    if parse_error is not None and not isinstance(parse_error, str):
        raise ValueError("Invalid parse_error")

    if record["execution"]["error"]:
        if json_validity is not None or parse_error is not None:
            raise ValueError("Failed requests must not have parsing verdicts")
    elif expects_json_response(record["test_id"]):
        if type(json_validity) is not bool:
            raise ValueError("JSON tasks require a parsing verdict")
        if json_validity and parse_error is not None:
            raise ValueError("Valid JSON must not have a parse error")
        if not json_validity and not parse_error:
            raise ValueError("Invalid JSON requires a parse error")
    elif json_validity is not None or parse_error is not None:
        raise ValueError("Text tasks must not have JSON parsing verdicts")

    if not isinstance(output["raw_response"], str):
        raise ValueError("Invalid raw_response")

    if not (
        output["parsed_response"] is None
        or isinstance(
            output["parsed_response"],
            (dict, list, str),
        )
    ):
        raise ValueError("Invalid parsed_response")

    execution = record["execution"]
    latency = execution["latency_ms"]
    if (
        type(latency) not in (int, float)
        or not 0 <= latency < float("inf")
    ):
        raise ValueError("Invalid latency_ms")

    if type(execution["error"]) is not bool:
        raise ValueError("Invalid execution error")

    if (
        execution["error_message"] is not None
        and not isinstance(execution["error_message"], str)
    ):
        raise ValueError("Invalid error_message")

    evaluation = record["evaluation"]

    for category in (
        "automatic_metrics",
        "qualitative_metrics",
        "safety_metrics",
    ):
        if not isinstance(evaluation[category], dict):
            raise ValueError(f"Invalid {category}")

    qualitative = evaluation["qualitative_metrics"]
    safety = evaluation["safety_metrics"]

    if set(qualitative) != set(
        run_specification["qualitative_metrics"]
    ):
        raise ValueError("Qualitative metric keys mismatch")

    if set(safety) != set(
        run_specification["safety_metrics"]
    ):
        raise ValueError("Safety metric keys mismatch")

    score_min = rubric["score_range"]["minimum"]
    score_max = rubric["score_range"]["maximum"]

    for metric, score in qualitative.items():
        if metric not in rubric["qualitative_metrics"]:
            raise ValueError(f"Unknown qualitative metric: {metric}")

        if score is None:
            continue

        if (
            type(score) is not int
            or not score_min <= score <= score_max
        ):
            raise ValueError(
                f"Invalid qualitative score: {metric}={score}"
            )

    for metric, verdict in safety.items():
        if metric not in rubric["binary_metrics"]:
            raise ValueError(f"Unknown safety metric: {metric}")

        if verdict is None:
            continue

        permitted = set(
            rubric["binary_metrics"][metric]
        )

        if verdict not in permitted:
            raise ValueError(
                f"Invalid safety verdict: {metric}={verdict}"
            )

def model_directory_name(model_name: str) -> str:
    """Create a portable folder name for a model identifier."""

    readable_name = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        model_name,
    ).strip("_-")

    readable_name = readable_name[:40] or "unnamed"

    identifier_hash = hashlib.sha256(
        model_name.encode("utf-8")
    ).hexdigest()[:16]

    return f"model-{readable_name}-{identifier_hash}"

def save_result_record(
    record: dict[str, Any],
    result_schema: dict[str, Any],
    rubric: dict[str, Any],
    run_specification: dict[str, Any],
) -> Path:
    """Validate and save one result as JSON."""

    validate_result_record(
        record,
        result_schema,
        rubric,
        run_specification,
    )

    destination = (
        RESULTS_DIR
        / record["test_id"]
        / record["provider"]
        / model_directory_name(record["model"])
    )

    destination.mkdir(parents=True, exist_ok=True)

    filename = (
        f"{record['case_id']}_"
        f"run_{record['run_number']}_"
        f"{record['run_id']}.json"
    )

    output_path = destination / filename

    with output_path.open(
        "x",
        encoding="utf-8",
    ) as file:
        json.dump(
            record,
            file,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )

    return output_path


# ============================================================
# MAIN
# ============================================================

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the academic AI benchmark."
    )

    parser.add_argument(
        "--provider",
        choices=["mock", "gemini"],
        default="mock",
        help="Provider to execute (mock or gemini).",
    )

    parser.add_argument(
        "--test",
        action="append",
        dest="tests",
        help="Test identifier. Repeat this option to select multiple tests.",
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help="Repetitions per case. Defaults to test_config.json.",
    )

    parser.add_argument(
        "--gemini-delay",
        type=float,
        default=8.0,
        help="Minimum delay between Gemini benchmark requests in seconds.",
    )

    arguments = parser.parse_args()

    if arguments.runs is not None and arguments.runs < 1:
        parser.error("--runs must be a positive integer")

    if arguments.gemini_delay < 0:
        parser.error("--gemini-delay cannot be negative")

    return arguments

def main() -> None:

    arguments = parse_arguments()
    print("Loading benchmark configuration...")

    configuration = load_benchmark_configuration()

    test_config = configuration["test_config"]

    if arguments.tests:
        requested_tests = set(arguments.tests)
        unknown_tests = requested_tests - set(test_config["tests"])

        if unknown_tests:
            raise SystemExit(
                "Unknown test identifier(s): "
                + ", ".join(sorted(unknown_tests))
            )

        test_config = {
            **test_config,
            "tests": {
                test_id: settings
                for test_id, settings in test_config["tests"].items()
                if test_id in requested_tests
            },
        }

    print("Building benchmark cases...")

    benchmark_cases = build_test_cases(
        test_config
    )

    print("Validating benchmark cases...")

    validate_benchmark_cases(
        benchmark_cases
    )

    runs_per_test_case = (
        arguments.runs
        if arguments.runs is not None
        else test_config["runs_per_test_case"]
    )

    print_benchmark_summary(
        benchmark_cases,
        runs_per_test_case,
    )

    print()
    print("Rendering prompts and building run specifications...")

    run_specifications = build_run_specifications(
        benchmark_cases,
        runs_per_test_case,
    )

    expected_run_count = (
        len(benchmark_cases)
        * runs_per_test_case
    )

    print("Validating run specifications...")

    validate_run_specifications(
        run_specifications,
        expected_run_count,
    )

    print_run_summary(
        run_specifications
    )
    
    print()
    print("Testing provider interface...")

    provider = create_provider(arguments.provider)
    batch_id = str(uuid4())
    print(f"Batch ID: {batch_id}")

    saved_count = 0
    provider_error_count = 0

    print()
    print(f"Executing {len(run_specifications)} benchmark runs...")

    last_request_started = None

    for index, run in enumerate(run_specifications, start=1):
        if arguments.provider == "gemini":
            if last_request_started is not None:
                elapsed = time.monotonic() - last_request_started
                remaining = arguments.gemini_delay - elapsed

                if remaining > 0:
                    print(f"Gemini pacing: waiting {remaining:.1f}s")
                    time.sleep(remaining)

            last_request_started = time.monotonic()

        result = execute_run(
            run_specification=run,
            provider=provider,
        )

        record = build_result_record(
            run_specification=run,
            result=result,
            batch_id=batch_id,
        )

        output_path = save_result_record(
            record=record,
            result_schema=configuration["result_schema"],
            rubric=configuration["rubric"],
            run_specification=run,
        )

        if load_json(output_path) != record:
            raise RuntimeError(
                f"Stored record mismatch: {output_path}"
            )

        saved_count += 1
        provider_error_count += int(result["error"])

        print(
            f"[{index}/{len(run_specifications)}] "
            f"{run['test_id']} | {run['case_id']} | "
            f"run {run['run_number']} | "
            f"provider_error={result['error']} | saved"
        )

    print()
    print("=" * 60)
    print("BENCHMARK EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Planned runs: {len(run_specifications)}")
    print(f"Executed and saved: {saved_count}")
    print(f"Provider errors: {provider_error_count}")
    print("Answer quality is recorded separately in each result.")
    print("Benchmark configuration validated successfully.")


if __name__ == "__main__":
    main()