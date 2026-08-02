from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.academic_positions.service import (
    get_position_by_id,
)
from app.auth.permissions import require_roles
from app.core.database import get_db
from app.evaluation_committees.schemas import (
    EvaluationCommitteeCreate,
    EvaluationCommitteeRead,
    EvaluationCommitteeUpdate,
)
from app.evaluation_committees.service import (
    create_evaluation_committee,
    delete_evaluation_committee,
    get_evaluation_committee_by_id,
    get_evaluation_committee_by_position,
    get_evaluation_committees,
    update_evaluation_committee,
)
from app.users.models import User


router = APIRouter(
    prefix="/evaluation-committees",
    tags=["Evaluation Committees"],
)


@router.post(
    "/",
    response_model=EvaluationCommitteeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_new_evaluation_committee(
    committee_data: EvaluationCommitteeCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    position = get_position_by_id(
        db,
        committee_data.position_id,
    )

    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic position not found",
        )

    existing_committee = (
        get_evaluation_committee_by_position(
            db,
            committee_data.position_id,
        )
    )

    if existing_committee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An evaluation committee already "
                "exists for this position"
            ),
        )

    return create_evaluation_committee(
        db=db,
        committee_data=committee_data,
        created_by=current_admin.id,
    )


@router.get(
    "/",
    response_model=list[EvaluationCommitteeRead],
)
def read_evaluation_committees(
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
            "REVIEWER",
        )
    ),
):
    return get_evaluation_committees(db)


@router.get(
    "/position/{position_id}",
    response_model=EvaluationCommitteeRead,
)
def read_evaluation_committee_by_position(
    position_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
            "REVIEWER",
        )
    ),
):
    committee = (
        get_evaluation_committee_by_position(
            db,
            position_id,
        )
    )

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation committee not found",
        )

    return committee


@router.get(
    "/{committee_id}",
    response_model=EvaluationCommitteeRead,
)
def read_evaluation_committee(
    committee_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
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

    return committee


@router.put(
    "/{committee_id}",
    response_model=EvaluationCommitteeRead,
)
def edit_evaluation_committee(
    committee_id: int,
    committee_data: EvaluationCommitteeUpdate,
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

    return update_evaluation_committee(
        db=db,
        committee=committee,
        committee_data=committee_data,
    )


@router.delete(
    "/{committee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_evaluation_committee(
    committee_id: int,
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

    if committee.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only draft evaluation committees "
                "can be deleted"
            ),
        )

    delete_evaluation_committee(
        db,
        committee,
    )