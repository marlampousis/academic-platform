
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


def calculate_category_presence(
    raw_response: str,
    required_facts: dict[str, Any],
) -> dict[str, Any]:
    """
    Approximate required-category coverage.

    This is a rule-based mention check, not semantic
    factual verification.
    """
    text = normalize_for_coverage(raw_response)

    # Positive research-output indicators.
    publication_pattern = (
        r"\b(?:publications?|journal articles?|"
        r"conference papers?)\b"
    )

    # Reject simple negative statements.
    publication_negative = (
        r"\b(?:no|without|never)\s+"
        r"(?:\w+\s+){0,3}"
        r"(?:publications?|journal articles?|conference papers?)\b"
    )

    project_pattern = r"\b(?:research\s+)?projects?\b"
    project_negative = (
        r"\b(?:no|without|never)\s+"
        r"(?:\w+\s+){0,3}(?:research\s+)?projects?\b"
    )

    has_publication = (
        bool(re.search(publication_pattern, text))
        and not bool(re.search(publication_negative, text))
    )

    has_project = (
        bool(re.search(project_pattern, text))
        and not bool(re.search(project_negative, text))
    )

    # Reuse the existing conservative reference checks.
    existing = calculate_required_facts_coverage(
        raw_response,
        required_facts,
    )["required_facts_checks"]

    checks = {
        **existing,
        "publications": has_publication,
        "research_projects": has_project,
    }

    return {
        "category_presence_coverage":
            sum(checks.values()) / len(checks),
        "category_presence_checks": checks,
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

    category_presence = calculate_category_presence(
        raw_response,
        expected_data["required_facts"],
    )

    return {
        "word_count": word_count,
        "word_count_compliance": word_count_compliance,
        **coverage,
        **category_presence,
    }
