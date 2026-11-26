
from sqlalchemy.orm import Session

from app.ai.models import AIRun, AIArtifact, utc_now
from app.ai.schemas.matching import (
    AcademicMatchingDraft,
    PositionRequirements,
)
from app.ai.services.persistence_service import create_ai_run


class MatchingPersistenceError(Exception):
    """Matching audit record could not be saved."""


def start_matching_run(
    db: Session,
    *,
    user_id: int,
    model_name: str,
) -> int:
    """Create a persistent audit entry before the AI call."""

    if user_id <= 0 or not model_name.strip():
        raise ValueError("Invalid matching run metadata")

    try:
        run = create_ai_run(
            db,
            user_id=user_id,
            task_type="ACADEMIC_MATCHING",
            provider="gemini",
            model_name=model_name,
        )

        run.status = "RUNNING"
        run_id = run.id
        db.commit()
        return run_id

    except Exception as exc:
        db.rollback()
        raise MatchingPersistenceError(
            "Could not initialize matching audit run"
        ) from exc


def complete_matching_run(
    db: Session,
    *,
    run_id: int,
    user_id: int,
    application_id: int,
    requirements: PositionRequirements,
    draft: AcademicMatchingDraft,
    latency_ms: int,
) -> int:
    """Atomically save the matching draft and successful run."""

    if (
        draft.application_id != application_id
        or draft.position_id != requirements.position_id
        or not draft.requires_human_review
    ):
        raise ValueError("Matching audit identities are invalid")

    if latency_ms < 0:
        raise ValueError("Latency cannot be negative")

    try:
        run = db.get(AIRun, run_id)

        if (
            run is None
            or run.user_id != user_id
            or run.task_type != "ACADEMIC_MATCHING"
            or run.status != "RUNNING"
        ):
            raise MatchingPersistenceError(
                "Matching run is missing or not writable"
            )

        artifact = AIArtifact(
            run_id=run_id,
            owner_user_id=user_id,
            application_id=application_id,
            artifact_type="ACADEMIC_MATCHING",
            status="REVIEW_REQUIRED",
            version=1,
            payload_json={
                "position_requirements": (
                    requirements.model_dump(mode="json")
                ),
                "matching_draft": (
                    draft.model_dump(mode="json")
                ),
            },
        )

        db.add(artifact)
        db.flush()

        artifact_id = artifact.id

        run.status = "SUCCEEDED"
        run.latency_ms = latency_ms
        run.error_code = None
        run.completed_at = utc_now()

        db.commit()

        return artifact_id

    except Exception as exc:
        db.rollback()

        if isinstance(exc, MatchingPersistenceError):
            raise

        raise MatchingPersistenceError(
            "Could not save matching audit artifact"
        ) from exc


def fail_matching_run(
    db: Session,
    *,
    run_id: int,
    error_code: str,
    latency_ms: int,
) -> None:
    """Record a failed run without saving a matching artifact."""

    if not error_code or len(error_code) > 100:
        raise ValueError("Invalid error code")

    if latency_ms < 0:
        raise ValueError("Latency cannot be negative")

    try:
        run = db.get(AIRun, run_id)

        if (
            run is None
            or run.task_type != "ACADEMIC_MATCHING"
            or run.status != "RUNNING"
        ):
            raise MatchingPersistenceError(
                "Matching run cannot be marked failed"
            )

        run.status = "FAILED"
        run.error_code = error_code
        run.latency_ms = latency_ms
        run.completed_at = utc_now()

        db.commit()

    except Exception as exc:
        db.rollback()

        if isinstance(exc, MatchingPersistenceError):
            raise

        raise MatchingPersistenceError(
            "Could not record matching failure"
        ) from exc
