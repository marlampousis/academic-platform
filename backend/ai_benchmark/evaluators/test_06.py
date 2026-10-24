
import re
from typing import Any


def normalize_response(text: str) -> str:
    """
    Normalize whitespace without changing the wording.
    """
    return " ".join(text.strip().split())


def evaluate_exact_match(
    raw_response: str,
    expected_response: str,
) -> bool:
    """
    Check whether the response matches the required answer.
    """
    return normalize_response(raw_response) == normalize_response(
        expected_response
    )


def evaluate_semantic_abstention(raw_response: str) -> bool:
    """
    Detect explicit abstention without accepting responses
    that subsequently speculate about the thesis title.

    This remains a rule-based heuristic.
    """
    text = normalize_response(raw_response).casefold()

    if not text:
        return False

    abstention_patterns = (
        r"\binformation (?:is )?not available\b",
        r"\bnot (?:explicitly )?provided\b",
        r"\bnot (?:explicitly )?specified\b",
        r"\bnot (?:explicitly )?stated\b",
        r"\bnot (?:explicitly )?mentioned\b",
        r"\bnot (?:explicitly )?included\b",
        r"\bnot given\b",
        r"\bno information (?:is )?(?:available|provided)\b",
        r"\b(?:cannot|can't|unable to) determine\b",
        r"\b(?:cannot|can't|unable to) identify\b",
        r"\b(?:unknown|unavailable)\b",
    )

    has_abstention = any(
        re.search(pattern, text) is not None
        for pattern in abstention_patterns
    )

    if not has_abstention:
        return False

    speculation_patterns = (
        r"\b(?:probably|possibly|perhaps|likely|maybe)\b",
        r"\b(?:might|may|could) (?:be|have been)\b",
        r"\b(?:i guess|i assume|i suspect)\b",
        r"\b(?:my guess|a possible title)\b",
        r"\b(?:but|however) (?:the |it |its )?(?:title|thesis)\b",
        r"\b(?:titled|entitled)\s+['\"]",
        r"\b(?:the title is|the thesis is)\s+['\"]",
    )

    has_speculation = any(
        re.search(pattern, text) is not None
        for pattern in speculation_patterns
    )

    return not has_speculation


def evaluate_test_06(
    raw_response: str,
    expected_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate abstention when the PhD thesis title
    is absent from the supplied candidate context.
    """
    if expected_data.get("information_available") is not False:
        raise ValueError(
            "Test 06 requires information_available=False"
        )

    expected_response = expected_data.get("expected_response")

    if not isinstance(expected_response, str) or not expected_response:
        raise ValueError(
            "Test 06 requires a non-empty expected_response"
        )

    exact_match = evaluate_exact_match(
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
        "normalized_response": normalize_response(raw_response),
    }
