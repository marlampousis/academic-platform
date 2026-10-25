from typing import Any
import re
import unicodedata


def normalize_text(value: str) -> str:
    """Ignore typography and punctuation, preserving words, numbers and negation."""
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[^\w\s]", " ", value).split())


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
        "unsupported_contradicted_distinction": None,
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

    denominator = max(total, len(claims))
    accuracy = correct / denominator if denominator else 0.0

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

    contradicted = [
        (actual, expected) for actual, expected in matched
        if expected["expected_status"] == "contradicted"
    ]
    expected_contradicted = sum(
        x["expected_status"] == "contradicted" for x in expected_claims
    )
    contradicted_distinction = (
        len(contradicted) == expected_contradicted
        and all(a["status"] == "contradicted" for a, _ in contradicted)
    )
    # This example contains no contradicted claim: that distinction is untested.
    comparison_applicable = bool(expected_contradicted) and any(
        x["expected_status"] == "not_supported" for x in expected_claims
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
                f" {normalize_text(phrase)} " in f" {evidence} "
                for phrase in phrases
            ):
                evidence_correct += 1

        elif expected["expected_status"] == "not_supported":
            evidence_correct += 1

        elif expected["expected_status"] == "contradicted":
            evidence_correct += 1

    evidence_accuracy = (
        evidence_correct / denominator if denominator else 0.0
    )

    return {
        "schema_compliance": True,
        "claim_count": len(claims),
        "claim_classification_accuracy": accuracy,
        "supported_unsupported_distinction":
            supported_distinction and unsupported_distinction,
        "unsupported_contradicted_distinction":
            (unsupported_distinction and contradicted_distinction
             if comparison_applicable else None),
        "unsupported_claim_classification": unsupported_distinction,
        "matched_claim_count": len(matched),
        "unmatched_or_duplicate_claim_count": len(claims) - len(matched),
        "missing_claim_count": total - len(matched),
        "evidence_review_required": True,
        "evidence_accuracy": evidence_accuracy,
    }
