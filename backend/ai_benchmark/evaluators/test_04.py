from typing import Any

from .automatic import (
    calculate_precision,
    calculate_recall,
    calculate_f1,
)


def normalize_area(value: str) -> str:
    return " ".join(value.casefold().split())


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

        if (not isinstance(item["position_area"], str)
            or not item["position_area"].strip()):
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

        if (not isinstance(item["position_area"], str)
            or not item["position_area"].strip()):
            return False

        if (not isinstance(item["explanation"], str)
            or not item["explanation"].strip()):
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

    actual_aligned = {
        normalize_area(item["position_area"]): item
        for item in parsed_response["aligned_areas"]
    }

    actual_missing = {
        normalize_area(item["position_area"])
        for item in parsed_response["areas_not_demonstrated"]
    }
    
    
    aligned_area_names = [
        normalize_area(item["position_area"])
        for item in parsed_response["aligned_areas"]
    ]

    missing_area_names = [
        normalize_area(item["position_area"])
        for item in parsed_response["areas_not_demonstrated"]
    ]

    duplicate_aligned_areas = sorted({
        area
        for area in aligned_area_names
        if aligned_area_names.count(area) > 1
    })

    duplicate_missing_areas = sorted({
        area
        for area in missing_area_names
        if missing_area_names.count(area) > 1
    })

    true_positives = len(
        set(actual_aligned) & set(expected_aligned)
    )

    false_positives = len(
        set(actual_aligned) - set(expected_aligned)
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

    
    missing_union = actual_missing | expected_missing

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


    # This checks structural contradictions, not semantic grounding.
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
            set(actual_aligned) - set(expected_aligned)
        ),
        "unexpected_missing_areas": sorted(
            actual_missing - expected_missing
        ),
        "contradictory_areas": sorted(
            set(actual_aligned) & actual_missing
        ),
        
        "duplicate_aligned_areas": duplicate_aligned_areas,
        "duplicate_missing_areas": duplicate_missing_areas,
        "logical_consistency_scope": "duplicate_labels_and_cross_section_overlap",
        "logical_consistency": (
            not duplicate_aligned_areas
            and not duplicate_missing_areas
            and not (set(actual_aligned) & actual_missing)
        ),
    }
