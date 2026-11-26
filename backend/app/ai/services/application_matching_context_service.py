
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.applications.models import Application
from app.ai.schemas.candidate_context import CandidateAcademicContext
from app.ai.services.candidate_context_service import (
    get_candidate_academic_context,
)
from app.ai.services.position_context_service import (
    PositionContext,
    get_position_context,
)


class MatchingApplicationNotFound(Exception):
    """Application does not exist."""


class MatchingContextError(Exception):
    """Application has inconsistent relationships."""


@dataclass(frozen=True)
class ApplicationMatchingContext:
    application_id: int
    user_id: int
    application_status: str
    position: PositionContext
    candidate: CandidateAcademicContext


def get_application_matching_context(
    db: Session,
    *,
    application_id: int,
) -> ApplicationMatchingContext:

    if application_id <= 0:
        raise ValueError("Application ID must be positive")

    application = db.get(Application, application_id)

    if application is None:
        raise MatchingApplicationNotFound(
            "Application not found"
        )

    candidate = get_candidate_academic_context(
        db,
        profile_id=application.profile_id,
        expected_user_id=application.user_id,
    )

    position = get_position_context(
        db,
        position_id=application.position_id,
    )

    if (
        candidate.profile_id != application.profile_id
        or candidate.user_id != application.user_id
        or position.position_id != application.position_id
    ):
        raise MatchingContextError(
            "Application relationships are inconsistent"
        )

    return ApplicationMatchingContext(
        application_id=application.id,
        user_id=application.user_id,
        application_status=application.status,
        position=position,
        candidate=candidate,
    )
