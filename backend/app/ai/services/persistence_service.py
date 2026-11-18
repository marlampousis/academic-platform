
from sqlalchemy.orm import Session

from app.ai.models import AIRun, AIArtifact, AIEvidence
from app.ai.schemas.extraction import AcademicCVExtraction

from app.ai.services.evidence_validation import (
    validate_extraction_evidence,
)

class AIArtifactNotFound(Exception):
    """Artifact does not exist or is not accessible."""


def create_ai_run(
    db: Session,
    *,
    user_id: int,
    task_type: str,
    provider: str,
    model_name: str,
) -> AIRun:
    run = AIRun(
        user_id=user_id,
        task_type=task_type,
        provider=provider,
        model_name=model_name,
        status="PENDING",
    )

    db.add(run)
    db.flush()

    return run

def save_extraction_artifact(
    db: Session,
    *,
    run: AIRun,
    owner_user_id: int,
    extraction: AcademicCVExtraction,
    source_id: str,
    cv_text: str,
    source_hash: str | None = None,
) -> AIArtifact:
    if run.id is None:
        raise ValueError("AI run must be flushed before saving")

    if run.user_id != owner_user_id:
        raise ValueError("AI run owner does not match artifact owner")

    if run.task_type != "CV_EXTRACTION":
        raise ValueError("AI run has an unexpected task type")

    if run.status != "SUCCEEDED":
        raise ValueError("Only successful AI runs can produce artifacts")

    if not source_id.strip():
        raise ValueError("source_id cannot be empty")

    # Final evidence verification before database persistence.
    validate_extraction_evidence(
        extraction,
        cv_text=cv_text,
        source_id=source_id,
    )

    artifact = AIArtifact(
        run_id=run.id,
        owner_user_id=owner_user_id,
        artifact_type="CV_EXTRACTION",
        status="REVIEW_REQUIRED",
        payload_json=extraction.model_dump(mode="json"),
        version=1,
    )

    db.add(artifact)
    db.flush()

    collections = (
        ("degrees", extraction.degrees),
        ("publications", extraction.publications),
        ("research_projects", extraction.research_projects),
        ("teaching_experience", extraction.teaching_experience),
    )

    for collection_name, records in collections:
        for index, record in enumerate(records):
            for evidence in record.evidence:
                if evidence.source_id != source_id:
                    raise ValueError(
                        "Evidence references an unexpected source"
                    )

                db.add(
                    AIEvidence(
                        artifact_id=artifact.id,
                        source_type="CV_TEXT",
                        source_id=evidence.source_id,
                        source_hash=source_hash,
                        field_path=f"{collection_name}.{index}",
                        excerpt=evidence.excerpt,
                        start_char=evidence.start_char,
                        end_char=evidence.end_char,
                        verified=False,
                    )
                )

    db.flush()
    return artifact


def get_extraction_artifact(
    db: Session,
    *,
    artifact_id: int,
    owner_user_id: int,
) -> AIArtifact:
    artifact = (
        db.query(AIArtifact)
        .filter(
            AIArtifact.id == artifact_id,
            AIArtifact.owner_user_id == owner_user_id,
            AIArtifact.artifact_type == "CV_EXTRACTION",
        )
        .first()
    )

    if artifact is None:
        raise AIArtifactNotFound(
            "Extraction artifact not found"
        )

    return artifact
