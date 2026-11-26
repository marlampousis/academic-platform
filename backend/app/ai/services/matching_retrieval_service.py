
from dataclasses import dataclass

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.models import AIArtifact, AIRun
from app.ai.schemas.matching import (
    AcademicMatchingDraft,
    PositionRequirements,
)


class MatchingArtifactNotFound(Exception):
    """Artifact does not exist or is not accessible."""


class MatchingArtifactInvalid(Exception):
    """Saved matching artifact has invalid data."""


@dataclass(frozen=True)
class SavedMatchingReport:
    artifact_id: int
    run_id: int
    status: str
    requirements: PositionRequirements
    matching_draft: AcademicMatchingDraft


def get_saved_matching_report(
    db: Session,
    *,
    artifact_id: int,
    owner_user_id: int,
) -> SavedMatchingReport:

    if artifact_id <= 0 or owner_user_id <= 0:
        raise ValueError("Identifiers must be positive")

    artifact = db.get(AIArtifact, artifact_id)

    # Do not expose the existence of another user's report.
    if (
        artifact is None
        or artifact.owner_user_id != owner_user_id
        or artifact.artifact_type != "ACADEMIC_MATCHING"
    ):
        raise MatchingArtifactNotFound(
            "Matching report not found"
        )

    run = db.get(AIRun, artifact.run_id)

    if (
        run is None
        or run.user_id != owner_user_id
        or run.task_type != "ACADEMIC_MATCHING"
        or run.status != "SUCCEEDED"
    ):
        raise MatchingArtifactInvalid(
            "Matching audit record is inconsistent"
        )

    try:
        payload = artifact.payload_json

        requirements = PositionRequirements.model_validate(
            payload["position_requirements"]
        )

        draft = AcademicMatchingDraft.model_validate(
            payload["matching_draft"]
        )

    except (
        KeyError,
        TypeError,
        ValidationError,
    ) as exc:
        raise MatchingArtifactInvalid(
            "Saved matching payload is invalid"
        ) from exc

    if (
        draft.application_id != artifact.application_id
        or draft.position_id != requirements.position_id
        or not draft.requires_human_review
    ):
        raise MatchingArtifactInvalid(
            "Saved matching identities are inconsistent"
        )

    return SavedMatchingReport(
        artifact_id=artifact.id,
        run_id=run.id,
        status=artifact.status,
        requirements=requirements,
        matching_draft=draft,
    )
