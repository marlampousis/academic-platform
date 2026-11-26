
from app.ai.schemas.matching import (
    AcademicMatchingDraft,
    MatchFinding,
    PositionRequirements,
)
from app.ai.schemas.candidate_context import (
    CandidateAcademicContext,
)


class MatchingValidationError(Exception):
    """The AI matching result failed validation."""


def validate_matching_draft(
    *,
    draft: AcademicMatchingDraft,
    requirements: PositionRequirements,
    candidate: CandidateAcademicContext,
) -> None:

    expected_ids = {
        item.requirement_id
        for item in requirements.requirements
    }

    actual_ids = [
        item.requirement_id
        for item in draft.matches
    ]

    if len(actual_ids) != len(set(actual_ids)):
        raise MatchingValidationError(
            "Duplicate requirement findings"
        )

    if set(actual_ids) != expected_ids:
        raise MatchingValidationError(
            "Matching draft must cover every "
            "position requirement exactly once"
        )

    valid_evidence = {
        "degrees": {
            item.id for item in candidate.degrees
        },
        "publications": {
            item.id for item in candidate.publications
        },
        "research_projects": {
            item.id for item in candidate.research_projects
        },
        "teaching_experience": {
            item.id for item in candidate.teaching_experience
        },
    }

    for match in draft.matches:
        seen = set()

        for evidence in match.evidence:
            collection = evidence.collection.value
            reference = (collection, evidence.record_id)

            if reference in seen:
                raise MatchingValidationError(
                    "Duplicate evidence reference"
                )

            seen.add(reference)

            if evidence.record_id not in valid_evidence[
                collection
            ]:
                raise MatchingValidationError(
                    "AI cited an academic record "
                    "outside the candidate profile"
                )

        if match.finding in (
            MatchFinding.SUPPORTED,
            MatchFinding.PARTIALLY_SUPPORTED,
        ) and not match.evidence:
            raise MatchingValidationError(
                "Supported findings require "
                "academic evidence references"
            )
    
        if match.finding in (
            MatchFinding.SUPPORTED,
            MatchFinding.PARTIALLY_SUPPORTED,
        ) and not match.evidence:
            raise MatchingValidationError(
                "Supported findings require "
                "academic evidence references"
            )


        if match.finding in (
            MatchFinding.PARTIALLY_SUPPORTED,
            MatchFinding.INSUFFICIENT_EVIDENCE,
            MatchFinding.UNSUPPORTED,
        ):
            if not match.uncertainty or not match.uncertainty.strip():
                raise MatchingValidationError(
                    "Non-supported findings must explain "
                    "uncertainty or the reason for the gap"
                )

    if not draft.requires_human_review:
        raise MatchingValidationError(
            "Human review cannot be disabled"
        )
