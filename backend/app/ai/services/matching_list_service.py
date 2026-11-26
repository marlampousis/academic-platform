
from sqlalchemy.orm import Session

from app.ai.models import AIArtifact, AIRun


def list_saved_matching_reports(
    db: Session,
    *,
    application_id: int,
    owner_user_id: int,
) -> list[dict]:
    """List saved matching reports owned by a candidate."""

    if application_id <= 0 or owner_user_id <= 0:
        raise ValueError("Identifiers must be positive")

    artifacts = (
        db.query(AIArtifact)
        .join(
            AIRun,
            AIArtifact.run_id == AIRun.id,
        )
        .filter(
            AIArtifact.application_id == application_id,
            AIArtifact.owner_user_id == owner_user_id,
            AIArtifact.artifact_type == "ACADEMIC_MATCHING",
            AIRun.user_id == owner_user_id,
            AIRun.task_type == "ACADEMIC_MATCHING",
            AIRun.status == "SUCCEEDED",
        )
        .order_by(AIArtifact.created_at.desc(), AIArtifact.id.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "artifact_id": artifact.id,
            "run_id": artifact.run_id,
            "application_id": artifact.application_id,
            "status": artifact.status,
            "created_at": artifact.created_at,
        }
        for artifact in artifacts
    ]
