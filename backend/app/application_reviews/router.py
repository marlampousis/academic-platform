from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.application_reviews.schemas import (
    ApplicationReviewRead,
    ApplicationStatusUpdate,
)
from app.application_reviews.service import (
    get_application_for_review,
    get_applications_for_position,
    update_application_review_status,
)
from app.auth.permissions import require_roles
from app.core.database import get_db
from app.users.models import User


router = APIRouter(
    prefix="/admin",
    tags=["Application Reviews"],
)


@router.get(
    "/positions/{position_id}/applications",
    response_model=list[ApplicationReviewRead],
)
def read_position_applications(
    position_id: int,
    application_status: str | None = Query(
        default=None,
        alias="status",
    ),
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    return get_applications_for_position(
        db=db,
        position_id=position_id,
        application_status=application_status,
    )


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationReviewRead,
)
def read_application_for_review(
    application_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    return get_application_for_review(
        db=db,
        application_id=application_id,
    )


@router.patch(
    "/applications/{application_id}/status",
    response_model=ApplicationReviewRead,
)
def change_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    application = get_application_for_review(
        db=db,
        application_id=application_id,
    )

    return update_application_review_status(
        db=db,
        application=application,
        new_status=status_data.status,
    )