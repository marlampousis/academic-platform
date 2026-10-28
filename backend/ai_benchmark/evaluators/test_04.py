
from typing import Any

from .automatic import (
    calculate_precision,
    calculate_recall,
    calculate_f1,
)


def normalize_area(value: str) -> str:
    return " ".join(value.casefold().split())

def expand_position_area(
    value: str,
    known_areas: set[str],
) -> set[str]:
    """
    Recognize exact area names and explicitly grouped areas.

    Does not infer areas from general descriptive language.
    """

    text = normalize_area(value)

    if text in known_areas:
        return {text}

    # Accept explicit conjunctions such as:
    # "Artificial Intelligence and Machine Learning".
    parts = [
        part.strip()
        for part in text.split(" and ")
    ]

    if (
        len(parts) > 1
        and all(part in known_areas for part in parts)
    ):
        return set(parts)

    return set()

import re

def normalize_evidence(value: str) -> str:
    """Normalize evidence text for conservative matching."""
    value = value.casefold()
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


def evidence_matches(
    provided: str,
    acceptable: str,
) -> bool:
    """Match exact evidence or a complete phrase in context."""
    provided_normalized = normalize_evidence(provided)
    acceptable_normalized = normalize_evidence(acceptable)

    if not provided_normalized or not acceptable_normalized:
        return False

    if provided_normalized == acceptable_normalized:
        return True

    provided_tokens = provided_normalized.split()
    acceptable_tokens = acceptable_normalized.split()

    if len(acceptable_tokens) < 2:
        return False

    phrase_length = len(acceptable_tokens)

    return any(
        provided_tokens[index:index + phrase_length]
        == acceptable_tokens
        for index in range(
            len(provided_tokens) - phrase_length + 1
        )
    )


def validate_test_04_schema(
    response: Any,
) -> bool:
    if not isinstance(response, dict):
        return False

    if set(response) != {
        "aligned_areas",
        "areas_not_demonstrated",
        "overall_explanation",
    }:
        return False

    if not isinstance(response["aligned_areas"], list):
        return False

    if not isinstance(response["areas_not_demonstrated"], list):
        return False

    if (
        not isinstance(response["overall_explanation"], str)
        or not response["overall_explanation"].strip()
    ):
        return False

    for item in response["aligned_areas"]:
        if not isinstance(item, dict):
            return False

        if set(item) != {
            "position_area",
            "candidate_evidence",
            "explanation",
        }:
            return False

        if not isinstance(item["position_area"], str):
            return False

        if (
            not isinstance(item["explanation"], str)
            or not item["explanation"].strip()
        ):
            return False


        evidence = item["candidate_evidence"]

        if not isinstance(evidence, list) or not evidence:
            return False

        if not all(
            isinstance(x, str) and x.strip()
            for x in evidence
        ):
            return False

    for item in response["areas_not_demonstrated"]:
        if not isinstance(item, dict):
            return False

        if set(item) != {
            "position_area",
            "explanation",
        }:
            return False

        if not isinstance(item["position_area"], str):
            return False

        if not isinstance(item["explanation"], str):
            return False

    return True


def evaluate_test_04(
    parsed_response: Any,
    expected_data: dict[str, Any],
) -> dict[str, Any]:

    metric_names = (
        "alignment_area_precision",
        "alignment_area_recall",
        "alignment_area_f1",
        "missing_evidence_accuracy",
    )

    if not validate_test_04_schema(parsed_response):
        return {
            "schema_compliance": False,
            **{name: None for name in metric_names},
            "evidence_checks": {},
            "missing_evidence_checks": {},
        }

    expected_aligned = {
        normalize_area(item["position_area"]): item
        for item in expected_data["expected_aligned_areas"]
    }

    expected_missing = {
        normalize_area(area)
        for area in expected_data["expected_not_demonstrated_areas"]
    }

    known_areas = set(expected_aligned) | expected_missing

    actual_aligned = {}
    actual_missing = set()

    for item in parsed_response["aligned_areas"]:
        areas = expand_position_area(
            item["position_area"],
            known_areas,
        )

        for area in areas:
            actual_aligned.setdefault(area, item)

    for item in parsed_response["areas_not_demonstrated"]:
        areas = expand_position_area(
            item["position_area"],
            known_areas,
        )

        actual_missing.update(areas)

    unrecognized_aligned = [
        normalize_area(item["position_area"])
        for item in parsed_response["aligned_areas"]
        if not expand_position_area(
            item["position_area"],
            known_areas,
        )
    ]

    unrecognized_missing = [
        normalize_area(item["position_area"])
        for item in parsed_response["areas_not_demonstrated"]
        if not expand_position_area(
            item["position_area"],
            known_areas,
        )
    ]

    # Count occurrences AFTER expanding grouped areas.
    aligned_counts = {}
    missing_counts = {}

    for item in parsed_response["aligned_areas"]:
        areas = expand_position_area(
            item["position_area"],
            known_areas,
        )

        for area in areas:
            aligned_counts[area] = aligned_counts.get(area, 0) + 1

    for item in parsed_response["areas_not_demonstrated"]:
        areas = expand_position_area(
            item["position_area"],
            known_areas,
        )

        for area in areas:
            missing_counts[area] = missing_counts.get(area, 0) + 1

    duplicate_aligned_areas = sorted(
        area
        for area, count in aligned_counts.items()
        if count > 1
    )

    duplicate_missing_areas = sorted(
        area
        for area, count in missing_counts.items()
        if count > 1
    )

    # Each repeated area beyond the first is an extra prediction.
    extra_aligned_predictions = sum(
        count - 1
        for count in aligned_counts.values()
        if count > 1
    )


    true_positives = len(
        set(actual_aligned) & set(expected_aligned)
    )

    false_positives = (
        len(set(actual_aligned) - set(expected_aligned))
        + len(unrecognized_aligned)
        + extra_aligned_predictions
    )

    false_negatives = len(
        set(expected_aligned) - set(actual_aligned)
    )

    precision = calculate_precision(
        true_positives,
        false_positives,
    )

    recall = calculate_recall(
        true_positives,
        false_negatives,
    )

    f1 = calculate_f1(precision, recall)

    
    missing_union = (
        actual_missing
        | expected_missing
        | set(unrecognized_missing)
    )

    if not missing_union:
        missing_accuracy = 1.0
    else:
        missing_accuracy = (
            len(actual_missing & expected_missing)
            / len(missing_union)
        )


    evidence_checks = {}

    for area, expected_item in expected_aligned.items():
        actual_item = actual_aligned.get(area)

        if actual_item is None:
            evidence_checks[area] = False
            continue

        
        acceptable = expected_item["acceptable_evidence"]
        provided = actual_item["candidate_evidence"]

        evidence_checks[area] = any(
            evidence_matches(provided_item, acceptable_item)
            for provided_item in provided
            for acceptable_item in acceptable
        )


    missing_checks = {
        area: area in actual_missing
        for area in expected_missing
    }

    return {
        "schema_compliance": True,
        "alignment_area_precision": precision,
        "alignment_area_recall": recall,
        "alignment_area_f1": f1,
        "missing_evidence_accuracy": missing_accuracy,
        "evidence_checks": evidence_checks,
        "missing_evidence_checks": missing_checks,
        "unexpected_aligned_areas": sorted(
            (set(actual_aligned) - set(expected_aligned))
            | set(unrecognized_aligned)
        ),
        "unexpected_missing_areas": sorted(
            (actual_missing - expected_missing)
            | set(unrecognized_missing)
        ),
        "contradictory_areas": sorted(
            set(actual_aligned) & actual_missing
        ),
        
        "duplicate_aligned_areas": duplicate_aligned_areas,
        "duplicate_missing_areas": duplicate_missing_areas,
        "logical_consistency": (
            not duplicate_aligned_areas
            and not duplicate_missing_areas
            and not (set(actual_aligned) & actual_missing)
        ),
    }
