
import logging

from fastapi import APIRouter, Depends, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.orm import Session

from app.ai.schemas.matching import AcademicMatchingDraft
from app.ai.services.academic_matching_service import (
    AcademicMatchingError,
    AcademicMatchingService,
)
from app.ai.services.application_matching_context_service import (
    MatchingApplicationNotFound,
    get_application_matching_context,
)
from app.ai.services.position_requirements_service import (
    create_gemini_requirements_service,
    extract_requirements_for_position,
)
from app.applications.models import Application
from app.auth.permissions import require_roles
from app.core.config import settings
from app.core.database import get_db
from app.users.models import User

from time import perf_counter

from app.ai.services.matching_persistence_service import (
    MatchingPersistenceError,
    start_matching_run,
    complete_matching_run,
    fail_matching_run,
)

from app.ai.services.matching_retrieval_service import (
    MatchingArtifactNotFound,
    MatchingArtifactInvalid,
    get_saved_matching_report,
)

from app.ai.services.matching_list_service import (
    list_saved_matching_reports,
)

from app.ai.services.matching_evidence_service import (
    get_matching_evidence_details,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai/applications",
    tags=["AI Academic Matching"],
)

artifact_router = APIRouter(
    prefix="/ai/matching-artifacts",
    tags=["AI Academic Matching"],
)

candidate_access = require_roles("CANDIDATE")


def create_matching_service() -> AcademicMatchingService:
    model_name = settings.GEMINI_MODEL

    if not model_name or not settings.GOOGLE_API_KEY:
        raise ValueError("Gemini is not configured")

    model = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.GOOGLE_API_KEY,
        timeout=60,
        max_retries=2,
    )

    structured_model = model.with_structured_output(
        AcademicMatchingDraft,
        method="json_schema",
    )

    return AcademicMatchingService(
        runnable=structured_model,
    )



@router.post(
    "/{application_id}/matching-drafts",
    response_model=AcademicMatchingDraft,
)
def generate_matching_draft(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(candidate_access),
):
    # 1. Authorization before any AI call or audit write.
    application = db.get(Application, application_id)

    if application is None or application.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if application.status != "DRAFT":
        raise HTTPException(
            status_code=409,
            detail="Matching preview requires a draft application",
        )

    if not settings.GEMINI_MODEL or not settings.GOOGLE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Matching service is not configured",
        )

    # 2. Create the audit run before invoking Gemini.
    try:
        run_id = start_matching_run(
            db,
            user_id=current_user.id,
            model_name=settings.GEMINI_MODEL,
        )
    except MatchingPersistenceError as exc:
        logger.error(
            "Could not initialize matching audit for application %s",
            application_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Could not initialize matching audit",
        ) from exc

    started = perf_counter()

    try:
        # 3. Load the candidate and position.
        context = get_application_matching_context(
            db,
            application_id=application_id,
        )

        # 4. Extract the advertised position requirements.
        requirements_service = (
            create_gemini_requirements_service()
        )

        requirements = extract_requirements_for_position(
            db,
            position_id=context.position.position_id,
            extraction_service=requirements_service,
        )

        if not requirements.requirements:
            raise HTTPException(
                status_code=422,
                detail="No position requirements available",
            )

        # 5. Generate the evidence-validated matching draft.
        matching_service = create_matching_service()

        draft = matching_service.match(
            context=context,
            requirements=requirements,
        )

        # 6. Persist the report and successful audit atomically.
        latency_ms = int(
            (perf_counter() - started) * 1000
        )

        complete_matching_run(
            db,
            run_id=run_id,
            user_id=current_user.id,
            application_id=application_id,
            requirements=requirements,
            draft=draft,
            latency_ms=latency_ms,
        )

        # Preserve the current Streamlit response contract.
        return draft

    except Exception as exc:
        latency_ms = int(
            (perf_counter() - started) * 1000
        )

        if isinstance(exc, HTTPException):
            error_code = "MATCHING_INPUT_ERROR"
        elif isinstance(exc, AcademicMatchingError):
            error_code = "MATCHING_GENERATION_ERROR"
        elif isinstance(exc, MatchingPersistenceError):
            error_code = "MATCHING_PERSISTENCE_ERROR"
        else:
            error_code = "MATCHING_PROCESSING_ERROR"

        root_cause = exc.__cause__

        logger.warning(
            "Matching failed: application_id=%s, "
            "error_type=%s, cause_type=%s",
            application_id,
            type(exc).__name__,
            (
                type(root_cause).__name__
                if root_cause is not None
                else "None"
            ),
        )

        # Record failure; never leave an audit run RUNNING.
        try:
            fail_matching_run(
                db,
                run_id=run_id,
                error_code=error_code,
                latency_ms=latency_ms,
            )
        except MatchingPersistenceError as audit_exc:
            logger.error(
                "Could not finalize matching audit run %s",
                run_id,
            )
            raise HTTPException(
                status_code=500,
                detail="Could not finalize matching audit",
            ) from audit_exc

        if isinstance(exc, HTTPException):
            raise

        if isinstance(exc, MatchingPersistenceError):
            raise HTTPException(
                status_code=500,
                detail="Could not save matching audit",
            ) from exc

        if isinstance(exc, ValueError):
            raise HTTPException(
                status_code=503,
                detail="Matching service configuration error",
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="AI matching failed or evidence was invalid",
        ) from exc

@artifact_router.get("/{artifact_id}")
def read_saved_matching_report(
    artifact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(candidate_access),
):
    if artifact_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Invalid artifact ID",
        )

    try:
        report = get_saved_matching_report(
            db,
            artifact_id=artifact_id,
            owner_user_id=current_user.id,
        )

        return {
            "artifact_id": report.artifact_id,
            "run_id": report.run_id,
            "status": report.status,
            "position_requirements": (
                report.requirements.model_dump(mode="json")
            ),
            "matching_draft": (
                report.matching_draft.model_dump(mode="json")
            ),
        }

    except MatchingArtifactNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail="Matching report not found",
        ) from exc

    except MatchingArtifactInvalid as exc:
        logger.warning(
            "Invalid stored matching artifact: artifact_id=%s",
            artifact_id,
        )
        raise HTTPException(
            status_code=409,
            detail="Saved matching report is invalid",
        ) from exc


@router.get("/{application_id}/matching-artifacts")
def list_application_matching_artifacts(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(candidate_access),
):
    if application_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Invalid application ID",
        )

    application = db.get(Application, application_id)

    # Verify application ownership before listing artifacts.
    if (
        application is None
        or application.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return list_saved_matching_reports(
        db,
        application_id=application_id,
        owner_user_id=current_user.id,
    )


@artifact_router.get("/{artifact_id}/evidence")
def read_matching_evidence_details(
    artifact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(candidate_access),
):
    """
    Return current official academic evidence cited by
    a saved matching artifact.

    Requires authenticated candidate ownership.
    Does not call Gemini or modify the database.
    """

    if artifact_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Invalid artifact ID",
        )

    try:
        return get_matching_evidence_details(
            db,
            artifact_id=artifact_id,
            owner_user_id=current_user.id,
        )

    except MatchingArtifactNotFound as exc:
        # Do not reveal whether another user's artifact exists.
        raise HTTPException(
            status_code=404,
            detail="Matching report not found",
        ) from exc

    except MatchingArtifactInvalid as exc:
        logger.warning(
            "Matching evidence unavailable: "
            "artifact_id=%s, error_type=%s",
            artifact_id,
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=409,
            detail="Matching evidence is unavailable or inconsistent",
        ) from exc