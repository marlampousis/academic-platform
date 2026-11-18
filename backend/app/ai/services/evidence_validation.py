
from app.ai.schemas.extraction import AcademicCVExtraction


class EvidenceValidationError(ValueError):
    """Evidence does not match the supplied source text."""


def validate_extraction_evidence(
    extraction: AcademicCVExtraction,
    *,
    cv_text: str,
    source_id: str,
) -> None:
    if not cv_text.strip():
        raise EvidenceValidationError("CV text cannot be empty")

    if not source_id.strip():
        raise EvidenceValidationError("source_id cannot be empty")

    records = (
        extraction.degrees
        + extraction.publications
        + extraction.research_projects
        + extraction.teaching_experience
    )

    for record in records:
        if not record.evidence:
            raise EvidenceValidationError(
                "An extracted record has no source evidence"
            )

        for evidence in record.evidence:
            if evidence.source_id != source_id:
                raise EvidenceValidationError(
                    "Evidence references an unexpected source"
                )

            if evidence.excerpt not in cv_text:
                raise EvidenceValidationError(
                    "Evidence excerpt was not found in the CV"
                )

            start = evidence.start_char
            end = evidence.end_char

            if (start is None) != (end is None):
                raise EvidenceValidationError(
                    "Evidence offsets must be provided together"
                )

            if start is not None:
                if cv_text[start:end] != evidence.excerpt:
                    raise EvidenceValidationError(
                        "Evidence offsets do not match the CV"
                    )
