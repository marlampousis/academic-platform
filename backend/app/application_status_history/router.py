from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application_reviews.service import (
    get_application_for_review,
)
from app.application_status_history.schemas import (
    ApplicationStatusHistoryRead,
)
from app.application_status_history.service import (
    get_application_status_history,
)
from app.auth.permissions import require_roles
from app.core.database import get_db
from app.users.models import User


router = APIRouter(
    prefix="/admin/applications",
    tags=["Application Status History"],
)


@router.get(
    "/{application_id}/history",
    response_model=list[ApplicationStatusHistoryRead],
)
def read_application_status_history(
    application_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    get_application_for_review(
        db=db,
        application_id=application_id,
    )

    return get_application_status_history(
        db=db,
        application_id=application_id,
    )