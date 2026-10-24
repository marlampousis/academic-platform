
import re
import unicodedata
from typing import Any

from .automatic import (
    calculate_word_count,
    calculate_word_count_compliance,
)


MIN_WORDS = 100
MAX_WORDS = 150


def normalize_for_coverage(value: str) -> str:
    """
    Normalize text for conservative phrase matching.
    """
    value = unicodedata.normalize("NFKC", value)
    value = value.casefold()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def contains_fact(text: str, fact: str) -> bool:
    """
    Check whether a complete fact phrase appears in text.
    """
    normalized_text = normalize_for_coverage(text)
    normalized_fact = normalize_for_coverage(fact)

    if not normalized_fact:
        return False

    return (
        f" {normalized_fact} "
        in f" {normalized_text} "
    )


def contains_any_fact(
    text: str,
    facts: list[str],
) -> bool:
    return any(
        contains_fact(text, fact)
        for fact in facts
    )


def calculate_required_facts_coverage(
    raw_response: str,
    required_facts: dict[str, Any],
) -> dict[str, Any]:
    """
    Measure explicit lexical coverage of six academic
    information categories.

    This is not a semantic completeness score.
    """

    research_evidence = required_facts.get(
        "research_evidence", {}
    )

    checks = {
        "specialization": contains_fact(
            raw_response,
            required_facts.get("specialization", ""),
        ),
        "research_areas": contains_any_fact(
            raw_response,
            required_facts.get("research_areas", []),
        ),
        "education": contains_any_fact(
            raw_response,
            required_facts.get("degrees", []),
        ),
        "publications": contains_any_fact(
            raw_response,
            research_evidence.get("publication_titles", []),
        ),
        "research_projects": contains_any_fact(
            raw_response,
            research_evidence.get("research_project_titles", []),
        ),
        "teaching_experience": contains_any_fact(
            raw_response,
            required_facts.get("teaching_courses", []),
        ),
    }

    covered = sum(checks.values())
    total = len(checks)

    return {
        "required_facts_coverage": covered / total,
        "required_facts_checks": checks,
    }


def evaluate_test_02(
    raw_response: str,
    expected_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate objective Test 02 constraints and
    explicit lexical evidence coverage.
    """

    constraints = expected_data.get("constraints", {})

    minimum = constraints["min_words"]
    maximum = constraints["max_words"]

    word_count = calculate_word_count(raw_response)

    word_count_compliance = (
        calculate_word_count_compliance(
            raw_response,
            minimum,
            maximum,
        )
    )

    coverage = calculate_required_facts_coverage(
        raw_response,
        expected_data["required_facts"],
    )

    return {
        "word_count": word_count,
        "word_count_compliance": word_count_compliance,
        **coverage,
    }
