from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.auth.permissions import require_roles
from app.core.database import get_db
from app.evaluation_committees.service import (
    get_evaluation_committee_by_id,
)
from app.evaluation_criteria.schemas import (
    EvaluationCriteriaSummary,
    EvaluationCriterionCreate,
    EvaluationCriterionRead,
    EvaluationCriterionUpdate,
)
from app.evaluation_criteria.service import (
    create_evaluation_criterion,
    delete_evaluation_criterion,
    get_evaluation_criteria,
    get_evaluation_criterion_by_code,
    get_evaluation_criterion_by_id,
    get_total_active_weight,
    update_evaluation_criterion,
)
from app.users.models import User


router = APIRouter(
    prefix="/evaluation-committees",
    tags=["Evaluation Criteria"],
)


def ensure_draft_committee(
    committee_status: str,
) -> None:
    if committee_status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Evaluation criteria can only be "
                "managed while the committee is DRAFT"
            ),
        )


@router.post(
    "/{committee_id}/criteria",
    response_model=EvaluationCriterionRead,
    status_code=status.HTTP_201_CREATED,
)
def add_evaluation_criterion(
    committee_id: int,
    criterion_data: EvaluationCriterionCreate,
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

    ensure_draft_committee(
        committee.status
    )

    existing_criterion = (
        get_evaluation_criterion_by_code(
            db=db,
            committee_id=committee_id,
            code=criterion_data.code,
        )
    )

    if existing_criterion:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An evaluation criterion with "
                "this code already exists"
            ),
        )

    current_weight = get_total_active_weight(
        db,
        committee_id,
    )

    resulting_weight = current_weight

    if criterion_data.is_active:
        resulting_weight += criterion_data.weight

    if resulting_weight > Decimal("100"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The total active criteria weight "
                "cannot exceed 100"
            ),
        )

    return create_evaluation_criterion(
        db=db,
        committee_id=committee_id,
        criterion_data=criterion_data,
        created_by=current_admin.id,
    )


@router.get(
    "/{committee_id}/criteria",
    response_model=list[EvaluationCriterionRead],
)
def read_evaluation_criteria(
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

    return get_evaluation_criteria(
        db=db,
        committee_id=committee_id,
    )


@router.get(
    "/{committee_id}/criteria/summary",
    response_model=EvaluationCriteriaSummary,
)
def read_evaluation_criteria_summary(
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

    criteria = get_evaluation_criteria(
        db=db,
        committee_id=committee_id,
    )

    total_active_weight = (
        get_total_active_weight(
            db,
            committee_id,
        )
    )

    active_count = sum(
        1
        for criterion in criteria
        if criterion.is_active
    )

    return EvaluationCriteriaSummary(
        committee_id=committee_id,
        criteria_count=len(criteria),
        active_criteria_count=active_count,
        total_active_weight=total_active_weight,
        is_weight_complete=(
            total_active_weight
            == Decimal("100")
        ),
        criteria=criteria,
    )


@router.get(
    "/{committee_id}/criteria/{criterion_id}",
    response_model=EvaluationCriterionRead,
)
def read_evaluation_criterion(
    committee_id: int,
    criterion_id: int,
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

    criterion = get_evaluation_criterion_by_id(
        db,
        criterion_id,
    )

    if (
        not criterion
        or criterion.committee_id != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation criterion not found",
        )

    return criterion


@router.put(
    "/{committee_id}/criteria/{criterion_id}",
    response_model=EvaluationCriterionRead,
)
def edit_evaluation_criterion(
    committee_id: int,
    criterion_id: int,
    criterion_data: EvaluationCriterionUpdate,
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

    ensure_draft_committee(
        committee.status
    )

    criterion = get_evaluation_criterion_by_id(
        db,
        criterion_id,
    )

    if (
        not criterion
        or criterion.committee_id != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation criterion not found",
        )

    if (
        criterion_data.code is not None
        and criterion_data.code != criterion.code
    ):
        existing_code = (
            get_evaluation_criterion_by_code(
                db=db,
                committee_id=committee_id,
                code=criterion_data.code,
            )
        )

        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "An evaluation criterion with "
                    "this code already exists"
                ),
            )

    resulting_weight = (
        criterion_data.weight
        if criterion_data.weight is not None
        else criterion.weight
    )

    resulting_active = (
        criterion_data.is_active
        if criterion_data.is_active is not None
        else criterion.is_active
    )

    other_active_weight = get_total_active_weight(
        db=db,
        committee_id=committee_id,
        excluded_criterion_id=criterion.id,
    )

    total_resulting_weight = other_active_weight

    if resulting_active:
        total_resulting_weight += resulting_weight

    if total_resulting_weight > Decimal("100"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The total active criteria weight "
                "cannot exceed 100"
            ),
        )

    return update_evaluation_criterion(
        db=db,
        criterion=criterion,
        criterion_data=criterion_data,
    )


@router.delete(
    "/{committee_id}/criteria/{criterion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_evaluation_criterion(
    committee_id: int,
    criterion_id: int,
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

    ensure_draft_committee(
        committee.status
    )

    criterion = get_evaluation_criterion_by_id(
        db,
        criterion_id,
    )

    if (
        not criterion
        or criterion.committee_id != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation criterion not found",
        )

    delete_evaluation_criterion(
        db=db,
        criterion=criterion,
    )