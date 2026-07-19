from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.users.models import User
from app.users.router import get_current_user

from app.profiles.service import get_profile_by_user_id

from app.academic_positions.service import (
    get_position_by_id,
)

from app.applications.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationSubmissionRead,
    ApplicationValidationRead,
)

from app.applications.service import (
    create_application,
    delete_application,
    get_application_by_id,
    get_application_by_user_and_position,
    get_applications_by_user_id,
    submit_application,
    validate_application,
)


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post(
    "/",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_new_application(
    application_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    position = get_position_by_id(
        db,
        application_data.position_id,
    )

    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )

    if (
        not position.position_status
        or position.position_status.code != "OPEN"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Position is not open for applications",
        )

    today = date.today()

    if (
        position.application_start_date
        and today < position.application_start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application period has not started yet",
        )

    if today > position.application_deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application deadline has passed",
        )

    profile = get_profile_by_user_id(
        db,
        current_user.id,
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found",
        )

    existing_application = (
        get_application_by_user_and_position(
            db,
            current_user.id,
            application_data.position_id,
        )
    )

    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an application for this position",
        )

    return create_application(
        db=db,
        position_id=application_data.position_id,
        user_id=current_user.id,
        profile_id=profile.id,
    )


@router.get(
    "/me",
    response_model=list[ApplicationRead],
)
def read_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_applications_by_user_id(
        db,
        current_user.id,
    )

@router.get(
    "/{application_id}/validation",
    response_model=ApplicationValidationRead,
)
def validate_current_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = get_application_by_id(
        db,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You are not allowed to validate "
                "this application"
            ),
        )

    return validate_application(
        db,
        application,
    )
    
@router.post(
    "/{application_id}/submit",
    response_model=ApplicationSubmissionRead,
)
def submit_current_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = get_application_by_id(
        db,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You are not allowed to submit "
                "this application"
            ),
        )

    validation_result = validate_application(
        db,
        application,
    )

    if not validation_result["can_submit"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": (
                    "Application cannot be submitted"
                ),
                "validation": validation_result,
            },
        )

    return submit_application(
        db,
        application,
    )    
    
@router.get(
    "/{application_id}",
    response_model=ApplicationRead,
)
def read_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = get_application_by_id(
        db,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this application",
        )

    return application


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = get_application_by_id(
        db,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this application",
        )

    if application.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft applications can be deleted",
        )

    delete_application(
        db,
        application,
    )