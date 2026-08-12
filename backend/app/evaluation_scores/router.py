from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.auth.permissions import require_roles
from app.committee_applications.service import (
    get_committee_application_by_id,
)
from app.committee_members.service import (
    get_committee_member_by_user,
)
from app.core.database import get_db
from app.evaluation_committees.service import (
    get_evaluation_committee_by_id,
)
from app.evaluation_criteria.service import (
    get_evaluation_criterion_by_id,
)
from app.evaluation_scores.schemas import (
    EvaluationScoreCreate,
    EvaluationScoreRead,
    EvaluationScoreUpdate,
)
from app.evaluation_scores.service import (
    create_evaluation_score,
    delete_evaluation_score,
    get_evaluation_score_by_id,
    get_existing_evaluation_score,
    get_reviewer_scores,
    get_scores_for_assignment,
    update_evaluation_score,
)
from app.users.models import User


router = APIRouter(
    prefix="/evaluation-committees",
    tags=["Evaluation Scores"],
)


def validate_reviewer_access(
    db: Session,
    committee_id: int,
    reviewer_id: int,
):
    membership = get_committee_member_by_user(
        db=db,
        committee_id=committee_id,
        user_id=reviewer_id,
    )

    if not membership or not membership.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Reviewer is not an active member "
                "of this committee"
            ),
        )

    return membership


@router.post(
    "/{committee_id}/applications/"
    "{assignment_id}/scores",
    response_model=EvaluationScoreRead,
    status_code=status.HTTP_201_CREATED,
)
def add_evaluation_score(
    committee_id: int,
    assignment_id: int,
    score_data: EvaluationScoreCreate,
    db: Session = Depends(get_db),
    current_reviewer: User = Depends(
        require_roles("REVIEWER")
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
                "Scores can only be submitted "
                "for active committees"
            ),
        )

    validate_reviewer_access(
        db=db,
        committee_id=committee_id,
        reviewer_id=current_reviewer.id,
    )

    assignment = (
        get_committee_application_by_id(
            db,
            assignment_id,
        )
    )

    if (
        not assignment
        or assignment.committee_id
        != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee application not found",
        )

    if assignment.status != "IN_EVALUATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Scores can only be submitted while "
                "the application is IN_EVALUATION"
            ),
        )

    criterion = get_evaluation_criterion_by_id(
        db,
        score_data.criterion_id,
    )

    if (
        not criterion
        or criterion.committee_id
        != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation criterion not found",
        )

    if not criterion.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evaluation criterion is inactive",
        )

    if score_data.score > criterion.max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Score cannot exceed "
                f"{criterion.max_score}"
            ),
        )

    existing_score = get_existing_evaluation_score(
        db=db,
        committee_application_id=assignment.id,
        criterion_id=criterion.id,
        reviewer_id=current_reviewer.id,
    )

    if existing_score:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Reviewer has already scored "
                "this criterion"
            ),
        )

    return create_evaluation_score(
        db=db,
        committee_application_id=assignment.id,
        reviewer_id=current_reviewer.id,
        score_data=score_data,
    )
    
@router.get(
    "/{committee_id}/applications/"
    "{assignment_id}/scores/me",
    response_model=list[EvaluationScoreRead],
)
def read_my_evaluation_scores(
    committee_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
    current_reviewer: User = Depends(
        require_roles("REVIEWER")
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

    validate_reviewer_access(
        db=db,
        committee_id=committee_id,
        reviewer_id=current_reviewer.id,
    )

    assignment = (
        get_committee_application_by_id(
            db,
            assignment_id,
        )
    )

    if (
        not assignment
        or assignment.committee_id
        != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee application not found",
        )

    return get_reviewer_scores(
        db=db,
        committee_application_id=assignment.id,
        reviewer_id=current_reviewer.id,
    )
    
@router.get(
    "/{committee_id}/applications/"
    "{assignment_id}/scores",
    response_model=list[EvaluationScoreRead],
)
def read_all_evaluation_scores(
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

    assignment = (
        get_committee_application_by_id(
            db,
            assignment_id,
        )
    )

    if (
        not assignment
        or assignment.committee_id
        != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee application not found",
        )

    return get_scores_for_assignment(
        db=db,
        committee_application_id=assignment.id,
    )
    
@router.put(
    "/{committee_id}/applications/"
    "{assignment_id}/scores/{score_id}",
    response_model=EvaluationScoreRead,
)
def edit_evaluation_score(
    committee_id: int,
    assignment_id: int,
    score_id: int,
    score_data: EvaluationScoreUpdate,
    db: Session = Depends(get_db),
    current_reviewer: User = Depends(
        require_roles("REVIEWER")
    ),
):
    validate_reviewer_access(
        db=db,
        committee_id=committee_id,
        reviewer_id=current_reviewer.id,
    )

    assignment = (
        get_committee_application_by_id(
            db,
            assignment_id,
        )
    )

    if (
        not assignment
        or assignment.committee_id
        != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee application not found",
        )

    if assignment.status != "IN_EVALUATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Scores can only be modified while "
                "the application is IN_EVALUATION"
            ),
        )

    evaluation_score = (
        get_evaluation_score_by_id(
            db,
            score_id,
        )
    )

    if (
        not evaluation_score
        or evaluation_score.committee_application_id
        != assignment.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation score not found",
        )

    if evaluation_score.reviewer_id != current_reviewer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Reviewers can only modify "
                "their own scores"
            ),
        )

    if score_data.score is not None:
        criterion = evaluation_score.criterion

        if score_data.score > criterion.max_score:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Score cannot exceed "
                    f"{criterion.max_score}"
                ),
            )

    return update_evaluation_score(
        db=db,
        evaluation_score=evaluation_score,
        score_data=score_data,
    )
    
@router.delete(
    "/{committee_id}/applications/"
    "{assignment_id}/scores/{score_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_evaluation_score(
    committee_id: int,
    assignment_id: int,
    score_id: int,
    db: Session = Depends(get_db),
    current_reviewer: User = Depends(
        require_roles("REVIEWER")
    ),
):
    validate_reviewer_access(
        db=db,
        committee_id=committee_id,
        reviewer_id=current_reviewer.id,
    )

    assignment = (
        get_committee_application_by_id(
            db,
            assignment_id,
        )
    )

    if (
        not assignment
        or assignment.committee_id
        != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee application not found",
        )

    if assignment.status != "IN_EVALUATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Scores can only be deleted while "
                "the application is IN_EVALUATION"
            ),
        )

    evaluation_score = (
        get_evaluation_score_by_id(
            db,
            score_id,
        )
    )

    if (
        not evaluation_score
        or evaluation_score.committee_application_id
        != assignment.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation score not found",
        )

    if evaluation_score.reviewer_id != current_reviewer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Reviewers can only delete "
                "their own scores"
            ),
        )

    delete_evaluation_score(
        db=db,
        evaluation_score=evaluation_score,
    )