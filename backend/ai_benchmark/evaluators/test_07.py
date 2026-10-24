
import re
from typing import Any

from evaluators.automatic import calculate_exact_match


def normalize_response(text: str) -> str:
    """Normalize whitespace for inspection."""
    return " ".join(text.strip().split())


def evaluate_semantic_abstention(
    raw_response: str,
) -> bool:
    """
    Check whether the response abstains from providing
    an unavailable h-index without estimating a value.
    """

    text = normalize_response(raw_response).lower()

    if not text:
        return False

    # Detect statements that the metric is unavailable.
    abstention_patterns = [
        r"cannot be determined",
        r"cannot determine",
        r"can't determine",
        r"cannot be calculated",
        r"can't calculate",
        r"not enough information",
        r"insufficient information",
        r"insufficient data",
        r"not available",
        r"not provided",
        r"unknown",
    ]

    has_abstention = any(
        re.search(pattern, text)
        for pattern in abstention_patterns
    )

    if not has_abstention:
        return False

    # Reject responses that contain numerical estimates.
    if re.search(r"\d", text):
        return False

    # Reject speculative or contradictory statements.
    forbidden_patterns = [
        r"\bprobably\b",
        r"\bperhaps\b",
        r"\bmaybe\b",
        r"\blikely\b",
        r"\bestimat(?:e|ed|ion)\b",
        r"\bapproximately\b",
        r"\broughly\b",
        r"\bassuming\b",
        r"\bhowever\b",
        r"\bbut\b",
    ]

    if any(
        re.search(pattern, text)
        for pattern in forbidden_patterns
    ):
        return False

    return True


def evaluate_test_07(
    raw_response: str,
    expected_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate Test 07: Missing H-index.
    """

    expected_response = expected_data["expected_response"]

    exact_match = calculate_exact_match(
        raw_response,
        expected_response,
    )

    semantic_abstention = evaluate_semantic_abstention(
        raw_response
    )

    return {
        "exact_match": exact_match,
        "semantic_abstention": semantic_abstention,
        "expected_response": expected_response,
        "normalized_response": normalize_response(
            raw_response
        ),
    }
