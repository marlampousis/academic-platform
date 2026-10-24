import re
from typing import Any


def normalize_text(text: str) -> str:
    """
    Normalize text for exact-match comparisons.
    """

    return " ".join(
        text.strip().split()
    )


def calculate_exact_match(
    actual: str,
    expected: str,
) -> bool:
    """
    Compare two text responses after whitespace normalization.
    """

    return (
        normalize_text(actual)
        == normalize_text(expected)
    )


def calculate_word_count(text: str) -> int:
    """
    Count whitespace-separated words in a response.
    """

    return len(text.split())


def calculate_word_count_compliance(
    text: str,
    minimum: int,
    maximum: int,
) -> bool:
    """
    Check whether a response satisfies a required word range.
    """

    word_count = calculate_word_count(text)

    return minimum <= word_count <= maximum


def calculate_precision(
    true_positives: int,
    false_positives: int,
) -> float:
    """
    Calculate precision safely.
    """

    denominator = (
        true_positives
        + false_positives
    )

    if denominator == 0:
        return 0.0

    return true_positives / denominator


def calculate_recall(
    true_positives: int,
    false_negatives: int,
) -> float:
    """
    Calculate recall safely.
    """

    denominator = (
        true_positives
        + false_negatives
    )

    if denominator == 0:
        return 0.0

    return true_positives / denominator


def calculate_f1(
    precision: float,
    recall: float,
) -> float:
    """
    Calculate F1 score safely.
    """

    if precision + recall == 0:
        return 0.0

    return (
        2
        * precision
        * recall
        / (precision + recall)
    )


def contains_numeric_score(text: str) -> bool:
    """
    Detect common numeric score/rating patterns.

    Examples:
        8/10
        85%
        score: 4
        rating: 5
    """

    patterns = [
        r"\b\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\b",
        r"\b\d+(?:\.\d+)?\s*%",
        r"\bscore\s*[:=]\s*\d+(?:\.\d+)?\b",
        r"\brating\s*[:=]\s*\d+(?:\.\d+)?\b",
    ]

    lowered = text.lower()

    return any(
        re.search(pattern, lowered)
        for pattern in patterns
    )


def evaluate_basic_automatic_metrics(
    test_id: str,
    raw_response: str,
    parsed_response: Any,
    json_validity: bool | None,
    expected_data: dict[str, Any],
    requested_metrics: list[str],
) -> dict[str, Any]:
    """
    Evaluate generic automatic metrics that can be shared
    across multiple benchmark tests.

    Test-specific metrics will be added separately.
    """

    results: dict[str, Any] = {}

    if "json_validity" in requested_metrics:
        results["json_validity"] = json_validity

    if "word_count" in requested_metrics:
        results["word_count"] = (
            calculate_word_count(raw_response)
        )

    if "word_count_compliance" in requested_metrics:
        constraints = expected_data.get(
            "constraints",
            {}
        )

        minimum = constraints.get(
            "min_words",
            constraints.get("minimum_words"),
        )

        maximum = constraints.get(
            "max_words",
            constraints.get("maximum_words"),
        )

        if (
            minimum is not None
            and maximum is not None
        ):
            results["word_count_compliance"] = (
                calculate_word_count_compliance(
                    raw_response,
                    minimum,
                    maximum,
                )
            )
        else:
            results["word_count_compliance"] = None

    if "exact_match" in requested_metrics:
        expected_response = expected_data.get(
            "expected_response"
        )

        if expected_response is not None:
            results["exact_match"] = (
                calculate_exact_match(
                    raw_response,
                    expected_response,
                )
            )
        else:
            results["exact_match"] = None

    if "forbidden_score" in requested_metrics:
        results["forbidden_score"] = (
            contains_numeric_score(
                raw_response
            )
        )

    return results