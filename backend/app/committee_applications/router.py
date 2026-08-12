from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.applications.service import (
    get_application_by_id,
)
from app.auth.permissions import require_roles
from app.committee_applications.schemas import (
    CommitteeApplicationCreate,
    CommitteeApplicationRead,
    CommitteeApplicationUpdate,
)
from app.committee_applications.service import (
    create_committee_application,
    delete_committee_application,
    get_assignment_by_application,
    get_committee_application_by_id,
    get_committee_applications,
    update_committee_application,
)
from app.core.database import get_db
from app.evaluation_committees.service import (
    get_evaluation_committee_by_id,
)
from app.users.models import User


router = APIRouter(
    prefix="/evaluation-committees",
    tags=["Committee Applications"],
)


@router.post(
    "/{committee_id}/applications",
    response_model=CommitteeApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def assign_application_to_committee(
    committee_id: int,
    assignment_data: CommitteeApplicationCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    committee = get_evaluation_committee_by_id(
        db,
        committee_id,
    )

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation committee not found",
        )

    if committee.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Applications can only be assigned "
                "to an active committee"
            ),
        )

    application = get_application_by_id(
        db,
        assignment_data.application_id,
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if (
        application.position_id
        != committee.position_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Application does not belong to "
                "the committee's academic position"
            ),
        )

    if application.status != "ELIGIBLE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only eligible applications can "
                "be assigned for evaluation"
            ),
        )

    existing_assignment = (
        get_assignment_by_application(
            db,
            application.id,
        )
    )

    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Application is already assigned "
                "to an evaluation committee"
            ),
        )

    return create_committee_application(
        db=db,
        committee_id=committee_id,
        assignment_data=assignment_data,
        assigned_by=current_admin.id,
    )


@router.get(
    "/{committee_id}/applications",
    response_model=list[CommitteeApplicationRead],
)
def read_committee_applications(
    committee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
            "REVIEWER",
        )
    ),
):
    committee = get_evaluation_committee_by_id(
        db,
        committee_id,
    )

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation committee not found",
        )

    return get_committee_applications(
        db=db,
        committee_id=committee_id,
    )


@router.get(
    "/{committee_id}/applications/{assignment_id}",
    response_model=CommitteeApplicationRead,
)
def read_committee_application(
    committee_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
            "REVIEWER",
        )
    ),
):
    committee = get_evaluation_committee_by_id(
        db,
        committee_id,
    )

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation committee not found",
        )

    assignment = get_committee_application_by_id(
        db,
        assignment_id,
    )

    if (
        not assignment
        or assignment.committee_id != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee application not found",
        )

    return assignment


@router.put(
    "/{committee_id}/applications/{assignment_id}",
    response_model=CommitteeApplicationRead,
)
def edit_committee_application(
    committee_id: int,
    assignment_id: int,
    assignment_data: CommitteeApplicationUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    committee = get_evaluation_committee_by_id(
        db,
        committee_id,
    )

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation committee not found",
        )

    if committee.status not in {
        "ACTIVE",
        "COMPLETED",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Committee application assignments "
                "cannot be modified in this "
                "committee status"
            ),
        )

    assignment = get_committee_application_by_id(
        db,
        assignment_id,
    )

    if (
        not assignment
        or assignment.committee_id != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee application not found",
        )

    return update_committee_application(
        db=db,
        assignment=assignment,
        assignment_data=assignment_data,
    )


@router.delete(
    "/{committee_id}/applications/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_committee_application(
    committee_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    committee = get_evaluation_committee_by_id(
        db,
        committee_id,
    )

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation committee not found",
        )

    assignment = get_committee_application_by_id(
        db,
        assignment_id,
    )

    if (
        not assignment
        or assignment.committee_id != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee application not found",
        )

    if assignment.status != "ASSIGNED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only assignments in ASSIGNED "
                "status can be deleted"
            ),
        )

    delete_committee_application(
        db=db,
        assignment=assignment,
    )