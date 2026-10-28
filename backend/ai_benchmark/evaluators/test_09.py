import re
from typing import Any


def normalize_requirement(value: str) -> str:
    """Normalize requirement names for comparison."""
    return " ".join(value.casefold().split())


def validate_test_09_schema(
    parsed_response: Any,
    expected_schema: dict[str, Any],
) -> bool:
    """Validate the exact Test 09 JSON structure."""

    if not isinstance(parsed_response, dict):
        return False

    required_top = set(
        expected_schema["required_top_level_fields"]
    )

    if set(parsed_response) != required_top:
        return False

    gaps = parsed_response["potential_gaps"]
    limitations = parsed_response["limitations"]

    if not isinstance(gaps, list):
        return False

    if not isinstance(limitations, str):
        return False

    if not limitations.strip():
        return False

    required_gap_fields = set(
        expected_schema["potential_gap_required_fields"]
    )

    allowed_statuses = set(
        expected_schema["allowed_evidence_status_values"]
    )

    for gap in gaps:
        if not isinstance(gap, dict):
            return False

        if set(gap) != required_gap_fields:
            return False

        requirement = gap["position_requirement"]
        status = gap["candidate_evidence_status"]
        explanation = gap["explanation"]

        if not isinstance(requirement, str):
            return False

        if not requirement.strip():
            return False

        if not isinstance(status, str):
            return False

        if status not in allowed_statuses:
            return False

        if not isinstance(explanation, str):
            return False

        if not explanation.strip():
            return False

    return True


def evaluate_test_09(
    parsed_response: Any,
    expected_data: dict[str, Any],
    expected_schema: dict[str, Any],
) -> dict[str, Any]:

    schema_valid = validate_test_09_schema(
        parsed_response,
        expected_schema,
    )

    metrics = {
        "schema_compliance": schema_valid,
        "gap_precision": None,
        "gap_recall": None,
        "gap_f1": None,
    }

    if not schema_valid:
        return metrics

    expected_gaps = expected_data["expected_potential_gaps"]
    actual_gaps = parsed_response["potential_gaps"]

    expected_areas = {
        normalize_requirement(gap["position_requirement"])
        for gap in expected_gaps
    }

    ordered_areas = sorted(
        expected_areas,
        key=len,
        reverse=True,
    )

    covered_areas = set()
    false_positives = 0

    for gap in actual_gaps:
        text = normalize_requirement(
            gap["position_requirement"]
        )

        matched_areas = set()

        for area in ordered_areas:
            pattern = r"(?<!\w)" + re.escape(area) + r"(?!\w)"

            if re.search(pattern, text):
                matched_areas.add(area)
                text = re.sub(pattern, " ", text)

        new_areas = matched_areas - covered_areas

        if new_areas:
            covered_areas.update(new_areas)
        else:
            false_positives += 1

    true_positives = len(covered_areas)
    false_negatives = len(expected_areas - covered_areas)

    if not expected_areas and not actual_gaps:
        precision = 1.0
        recall = 1.0
    else:
        precision_denominator = (
            true_positives + false_positives
        )
        recall_denominator = (
            true_positives + false_negatives
        )

        precision = (
            true_positives / precision_denominator
            if precision_denominator
            else 0.0
        )

        recall = (
            true_positives / recall_denominator
            if recall_denominator
            else 0.0
        )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    metrics.update({
        "gap_precision": precision,
        "gap_recall": recall,
        "gap_f1": f1,
    })

    return metrics