
import re
from typing import Any


HEADINGS = (
    "Alignment Summary:",
    "Supporting Evidence:",
    "Areas Not Demonstrated:",
)


def normalize_text(value: str) -> str:
    return " ".join(
        value.casefold().split()
    )


def extract_sections(response: str) -> dict[str, str]:
    """
    Extract the three required Test 03 sections.
    """
    sections = {}

    for index, heading in enumerate(HEADINGS):
        start = response.find(heading)

        if start == -1:
            sections[heading] = ""
            continue

        start += len(heading)

        if index + 1 < len(HEADINGS):
            next_heading = HEADINGS[index + 1]
            end = response.find(next_heading, start)
        else:
            end = -1

        sections[heading] = response[
            start:end if end != -1 else None
        ].strip()

    return sections


def contains_area(text: str, area: str) -> bool:
    """
    Conservative literal area detection.
    """
    normalized_text = normalize_text(text)
    normalized_area = normalize_text(area)

    pattern = (
        r"(?<!\w)"
        + re.escape(normalized_area)
        + r"(?!\w)"
    )

    return bool(
        re.search(pattern, normalized_text)
    )


def detect_negative_qualification_claims(
    response: str,
    missing_areas: list[str],
) -> list[str]:
    """
    Detect explicit unsupported claims of missing qualifications.

    Conservative lexical check, not full semantic evaluation.
    """
    negative_patterns = (
        r"\blacks?\b",
        r"\bdoes not have\b",
        r"\bhas no\b",
        r"\bdoes not possess\b",
        r"\bwithout\b",
    )

    detected = []

    for area in missing_areas:
        area_pattern = re.escape(normalize_text(area))

        for sentence in re.split(r"(?<=[.!?])\s+|\n+", response):
            normalized_sentence = normalize_text(sentence)

            if not re.search(area_pattern, normalized_sentence):
                continue

            if any(
                re.search(pattern, normalized_sentence)
                for pattern in negative_patterns
            ):
                detected.append(area)
                break

    return detected

def evaluate_test_03(
    raw_response: str,
    expected_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate explicit mentions of expected alignment
    areas and missing-evidence areas.

    These are lexical proxy metrics, not a complete
    semantic or factual evaluation.
    """

    sections = extract_sections(raw_response)

    alignment_text = (
        sections["Alignment Summary:"]
        + "\n"
        + sections["Supporting Evidence:"]
    )

    missing_text = sections["Areas Not Demonstrated:"]

    expected_alignment = [
        item["area"]
        for item in expected_data[
            "supported_alignment_areas"
        ]
    ]

    expected_missing = expected_data[
        "areas_not_demonstrated"
    ]

    found_alignment = [
        area
        for area in expected_alignment
        if contains_area(alignment_text, area)
    ]

    found_missing = [
        area
        for area in expected_missing
        if contains_area(missing_text, area)
    ]
    
    
    unsupported_alignment = [
        area
        for area in expected_missing
        if contains_area(alignment_text, area)
    ]

    unsupported_alignment_checks = {
        area: area in unsupported_alignment
        for area in expected_missing
    }


    alignment_recall = (
        len(found_alignment) / len(expected_alignment)
        if expected_alignment else 1.0
    )

    # We cannot determine false positives reliably
    # from unrestricted free-text output.
    alignment_precision = None
    alignment_f1 = None

    if expected_missing:
        missing_accuracy = (
            len(found_missing) / len(expected_missing)
        )
    else:
        # Empty expected gaps require a separate
        # semantic check for invented gap claims.
        missing_accuracy = None

    
    negative_qualification_claims = (
        detect_negative_qualification_claims(
            raw_response,
            expected_missing,
        )
    )

    return {
        "alignment_area_precision": alignment_precision,
        "alignment_area_recall": alignment_recall,
        "alignment_area_f1": alignment_f1,
        "missing_evidence_accuracy": missing_accuracy,
        "unsupported_alignment_areas": unsupported_alignment,
        "unsupported_alignment_checks": unsupported_alignment_checks,
        "unsupported_alignment_detected": bool(
            unsupported_alignment
        ),
        "alignment_area_checks": {
            area: area in found_alignment
            for area in expected_alignment
        },
        "missing_evidence_checks": {
            area: area in found_missing
            for area in expected_missing
        },
        "section_presence": {
            heading: heading in raw_response
            for heading in HEADINGS
        },
        "negative_qualification_claims": negative_qualification_claims,
        "negative_qualification_claim_detected": bool(
            negative_qualification_claims
        ),
        
    }
