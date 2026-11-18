
import hashlib
import logging
import os
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.permissions import require_roles
from app.users.models import User

from app.ai.schemas.extraction import AcademicCVExtraction
from app.ai.services.extraction_service import (
    AIExtractionError,
    create_gemini_extraction_service,
)
from app.ai.services.persistence_service import (
    AIArtifactNotFound,
    create_ai_run,
    save_extraction_artifact,
    get_extraction_artifact,
)

from app.ai.services.evidence_validation import (
    EvidenceValidationError,
    validate_extraction_evidence,
)

from time import perf_counter

from app.core.config import settings
from app.ai.models import AIRun
from app.ai.models import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["AI Extraction"],
)

candidate_access = require_roles("CANDIDATE")


class ExtractionRequest(BaseModel):
    cv_text: str = Field(min_length=1, max_length=40000)


class ExtractionResponse(BaseModel):
    artifact_id: int
    run_id: int
    status: str
    source_id: str
    extraction: AcademicCVExtraction


def mark_ai_run_failed(
    db: Session,
    *,
    run_id: int,
    error_code: str,
    latency_ms: int,
) -> None:
    run = db.get(AIRun, run_id)

    if run is None:
        raise RuntimeError("AI run not found")

    run.status = "FAILED"
    run.error_code = error_code
    run.latency_ms = latency_ms
    run.completed_at = utc_now()

    db.commit()


@router.post(
    "/extractions",
    response_model=ExtractionResponse,
    status_code=status.HTTP_201_CREATED,
)

def create_extraction(
    request: ExtractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(candidate_access),
):
    cv_text = request.cv_text

    if not cv_text.strip():
        raise HTTPException(
            status_code=422,
            detail="CV text cannot be empty",
        )

    source_id = f"cv-{uuid4().hex}"
    source_hash = hashlib.sha256(
        cv_text.encode("utf-8")
    ).hexdigest()

    model_name = settings.GEMINI_MODEL or "unconfigured"

    # Phase 1: Persist the initial run.
    try:
        run = create_ai_run(
            db,
            user_id=current_user.id,
            task_type="CV_EXTRACTION",
            provider="gemini",
            model_name=model_name,
        )
        run.status = "RUNNING"
        db.commit()
        run_id = run.id

    except Exception:
        db.rollback()
        logger.exception("Could not create AI run")
        raise HTTPException(
            status_code=500,
            detail="Could not initialize AI extraction",
        )

    # Phase 2: Execute Gemini.
    started = perf_counter()

    try:
        extraction_service = create_gemini_extraction_service()

        extraction = extraction_service.extract(
            cv_text=cv_text,
            source_id=source_id,
        )
        
        # Independently validate all evidence before persistence.
        validate_extraction_evidence(
            extraction,
            cv_text=cv_text,
            source_id=source_id,
        )

    except (AIExtractionError, ValueError) as exc:
        latency_ms = int(
            (perf_counter() - started) * 1000
        )

        error_code = (
            "PROVIDER_CONFIGURATION_ERROR"
            if type(exc) is ValueError
            else "AI_EXTRACTION_ERROR"
        )

        try:
            mark_ai_run_failed(
                db,
                run_id=run_id,
                error_code=error_code,
                latency_ms=latency_ms,
            )
        except Exception:
            db.rollback()
            logger.exception("Could not record failed AI run")
            raise HTTPException(
                status_code=500,
                detail="Could not record AI extraction failure",
            )

        logger.warning(
            "AI run %s failed: %s",
            run_id,
            error_code,
        )

        if type(exc) is ValueError:
            raise HTTPException(
                status_code=503,
                detail="AI provider is not configured",
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="AI extraction failed or evidence was invalid",
        ) from exc

    latency_ms = int(
        (perf_counter() - started) * 1000
    )

    # Phase 3: Save the artifact and mark success
    # in the same database transaction.
    try:
        run = db.get(AIRun, run_id)

        if run is None:
            raise RuntimeError("AI run not found")

        run.status = "SUCCEEDED"
        run.latency_ms = latency_ms
        run.completed_at = utc_now()
        run.error_code = None

        artifact = save_extraction_artifact(
            db,
            run=run,
            owner_user_id=current_user.id,
            extraction=extraction,
            source_id=source_id,
            cv_text=cv_text,
            source_hash=source_hash,
        )

        artifact_id = artifact.id
        artifact_status = artifact.status

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("Failed to persist AI extraction")

        try:
            mark_ai_run_failed(
                db,
                run_id=run_id,
                error_code="PERSISTENCE_ERROR",
                latency_ms=latency_ms,
            )
        except Exception:
            db.rollback()
            logger.exception(
                "Could not record persistence failure"
            )

        raise HTTPException(
            status_code=500,
            detail="Could not save AI extraction",
        )

    return ExtractionResponse(
        artifact_id=artifact_id,
        run_id=run_id,
        status=artifact_status,
        source_id=source_id,
        extraction=extraction,
    )

@router.get(
    "/extractions/{artifact_id}",
)
def read_extraction(
    artifact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(candidate_access),
):
    try:
        artifact = get_extraction_artifact(
            db,
            artifact_id=artifact_id,
            owner_user_id=current_user.id,
        )

    except AIArtifactNotFound:
        raise HTTPException(
            status_code=404,
            detail="Extraction not found",
        )

    return {
        "artifact_id": artifact.id,
        "run_id": artifact.run_id,
        "status": artifact.status,
        "version": artifact.version,
        "extraction": artifact.payload_json,
    }
