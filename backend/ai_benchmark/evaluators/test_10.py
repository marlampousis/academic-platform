import re
import unicodedata
from typing import Any


def normalize_greek_text(text: str) -> str:
    """Normalize Greek and English text for phrase matching."""

    text = unicodedata.normalize("NFD", text)

    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )

    text = text.casefold()

    text = re.sub(r"[^\w\s]", " ", text)

    return " ".join(text.split())

def contains_phrase(text: str, phrase: str) -> bool:
    """Match a phrase without matching inside other words."""

    normalized_text = normalize_greek_text(text)
    normalized_phrase = normalize_greek_text(phrase)

    if not normalized_phrase:
        return False

    pattern = (
        r"(?<!\w)"
        + re.escape(normalized_phrase)
        + r"(?!\w)"
    )

    return re.search(pattern, normalized_text) is not None


def calculate_research_area_coverage(
    response: str,
    expected_data: dict[str, Any],
) -> float:
    """Calculate explicit research-area coverage."""

    core_facts = expected_data["expected_core_facts"]

    expected_areas = [
        core_facts["specialization"],
        *core_facts["research_areas"],
    ]

    if not expected_areas:
        return 1.0

    found = sum(
        contains_phrase(response, area)
        for area in expected_areas
    )

    return found / len(expected_areas)


def find_research_evidence(
    response: str,
    expected_data: dict[str, Any],
) -> list[str]:
    """Find exact known publication/project titles in response."""

    found_titles = []

    for item in expected_data["valid_research_evidence"]:
        title = item["title"]

        if contains_phrase(response, title):
            found_titles.append(title)

    return found_titles


def calculate_evidence_validity(
    response: str,
    expected_data: dict[str, Any],
) -> float:
    """
    Return a conservative evidence-recognition indicator.

    1.0 means at least one known evidence title was identified.
    0.0 means none was identified.

    This is not a complete factual-grounding assessment.
    """

    found = find_research_evidence(
        response,
        expected_data,
    )

    return 1.0 if found else 0.0


def count_enumerated_evidence_items(response: str) -> int:
    """Count explicit numbered/bulleted items, including unsupported evidence.

    This assumes list items are evidence items, as requested by this task.
    Prose and nested lists still require manual review.
    """
    pattern = r"(?m)^\s*(?:\*\*)?(?:[0-9]+[.)]|[-*•])\s+\S"
    return len(re.findall(pattern, response))


def calculate_maximum_item_compliance(
    response: str,
    expected_data: dict[str, Any],
) -> bool | None:
    """Check an explicit evidence list; leave ambiguous prose unassessed.

    Recognized titles provide a lower bound even without a list. Recognition
    alone cannot establish compliance because unknown evidence may be present.
    """
    maximum = expected_data["constraints"]["maximum_research_evidence_items"]
    recognized = len(find_research_evidence(response, expected_data))
    enumerated = count_enumerated_evidence_items(response)
    if max(recognized, enumerated) > maximum:
        return False
    if enumerated:
        return True
    return None


def calculate_greek_response(response: str) -> bool:
    """
    Check whether Greek letters are present and constitute
    a majority of Greek/Latin alphabetic characters.
    """

    greek_letters = 0
    latin_letters = 0

    for char in response:
        if "\u0370" <= char <= "\u03ff" or "\u1f00" <= char <= "\u1fff":
            if char.isalpha():
                greek_letters += 1

        elif ("a" <= char.lower() <= "z"):
            latin_letters += 1

    total = greek_letters + latin_letters

    return (
        total > 0
        and greek_letters > latin_letters
    )


def evaluate_test_10(
    raw_response: str,
    expected_data: dict[str, Any],
) -> dict[str, Any]:
    """Calculate Test 10-specific automatic metrics."""

    return {
        "research_area_coverage":
            calculate_research_area_coverage(
                raw_response,
                expected_data,
            ),

        "evidence_validity":
            calculate_evidence_validity(
                raw_response,
                expected_data,
            ),

        "maximum_item_compliance":
            calculate_maximum_item_compliance(
                raw_response,
                expected_data,
            ),

        "recognized_evidence_titles": find_research_evidence(
            raw_response, expected_data,
        ),
        "enumerated_evidence_items": count_enumerated_evidence_items(raw_response),
        "evidence_review_required": True,

        "greek_response":
            calculate_greek_response(
                raw_response,
            ),
    }
