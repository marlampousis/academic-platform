from typing import Any
import re


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def evaluate_test_12(
    parsed_response: Any,
    expected_data: dict[str, Any],
) -> dict[str, Any]:

    expected_claims = expected_data["expected_claims"]
    schema = expected_data["expected_schema"]

    default = {
        "schema_compliance": False,
        "claim_count": 0,
        "claim_classification_accuracy": 0.0,
        "supported_unsupported_distinction": False,
        "unsupported_contradicted_distinction": False,
        "evidence_accuracy": 0.0,
    }

    if not isinstance(parsed_response, dict):
        return default.copy()

    required_top = set(
        schema["required_top_level_fields"]
    )

    if set(parsed_response) != required_top:
        return default.copy()

    claims = parsed_response.get("claims")
    assessment = parsed_response.get("overall_assessment")

    if not isinstance(claims, list):
        return default.copy()

    if not isinstance(assessment, str):
        return default.copy()

    required_fields = set(
        schema["claim_required_fields"]
    )

    allowed_statuses = set(
        schema["allowed_status_values"]
    )

    valid_claims = all(
        isinstance(claim, dict)
        and set(claim) == required_fields
        and isinstance(claim.get("claim"), str)
        and bool(claim["claim"].strip())
        and isinstance(claim.get("status"), str)
        and claim["status"] in allowed_statuses
        and isinstance(claim.get("evidence"), str)
        for claim in claims
    )

    if not valid_claims:
        return {
            **default,
            "claim_count": len(claims),
        }

    expected_by_text = {
        normalize_text(item["claim"]): item
        for item in expected_claims
    }

    matched = []
    used = set()

    for claim in claims:
        key = normalize_text(claim["claim"])

        if key in expected_by_text and key not in used:
            matched.append(
                (claim, expected_by_text[key])
            )
            used.add(key)

    total = len(expected_claims)

    correct = sum(
        actual["status"] == expected["expected_status"]
        for actual, expected in matched
    )

    accuracy = correct / total if total else 0.0

    supported = [
        (actual, expected)
        for actual, expected in matched
        if expected["expected_status"] == "supported"
    ]

    unsupported = [
        (actual, expected)
        for actual, expected in matched
        if expected["expected_status"] == "not_supported"
    ]

    supported_distinction = (
        bool(supported)
        and all(
            actual["status"] == "supported"
            for actual, _ in supported
        )
        and len(supported) == sum(
            item["expected_status"] == "supported"
            for item in expected_claims
        )
    )

    unsupported_distinction = (
        bool(unsupported)
        and all(
            actual["status"] == "not_supported"
            for actual, _ in unsupported
        )
        and len(unsupported) == sum(
            item["expected_status"] == "not_supported"
            for item in expected_claims
        )
    )

    evidence_correct = 0

    for actual, expected in matched:

        if actual["status"] != expected["expected_status"]:
            continue

        evidence = normalize_text(actual["evidence"])

        if not evidence:
            continue

        if expected["expected_status"] == "supported":
            phrases = expected.get("supporting_evidence", [])

            if any(
                normalize_text(phrase) in evidence
                for phrase in phrases
            ):
                evidence_correct += 1

        elif expected["expected_status"] == "not_supported":
            evidence_correct += 1

        elif expected["expected_status"] == "contradicted":
            evidence_correct += 1

    evidence_accuracy = (
        evidence_correct / total if total else 0.0
    )

    return {
        "schema_compliance": True,
        "claim_count": len(claims),
        "claim_classification_accuracy": accuracy,
        "supported_unsupported_distinction":
            supported_distinction,
        "unsupported_contradicted_distinction":
            unsupported_distinction,
        "evidence_accuracy": evidence_accuracy,
    }
