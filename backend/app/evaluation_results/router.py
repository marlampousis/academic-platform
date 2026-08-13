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
from app.core.database import get_db
from app.evaluation_committees.service import (
    get_evaluation_committee_by_id,
)
from app.evaluation_results.schemas import (
    EvaluationDecisionUpdate,
    EvaluationResultRead,
    RankingItemRead,
)
from app.evaluation_results.service import (
    generate_committee_ranking,
    get_evaluation_result_by_assignment,
    set_final_decision,
)
from app.users.models import User


router = APIRouter(
    prefix="/evaluation-committees",
    tags=["Evaluation Results"],
)

@router.post(
    "/{committee_id}/ranking/generate",
    response_model=list[RankingItemRead],
)
def generate_ranking(
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

    ranked_results = generate_committee_ranking(
        db=db,
        committee_id=committee_id,
    )

    if not ranked_results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No applications with submitted "
                "evaluation reports are available"
            ),
        )

    return [
        RankingItemRead(
            committee_application_id=assignment.id,
            application_id=assignment.application_id,
            final_score=result.final_score,
            rank_position=result.rank_position,
            decision=result.decision,
        )
        for assignment, result in ranked_results
    ]
    
@router.get(
    "/{committee_id}/ranking",
    response_model=list[RankingItemRead],
)
def read_ranking(
    committee_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    ranked_results = generate_committee_ranking(
        db=db,
        committee_id=committee_id,
    )

    return [
        RankingItemRead(
            committee_application_id=assignment.id,
            application_id=assignment.application_id,
            final_score=result.final_score,
            rank_position=result.rank_position,
            decision=result.decision,
        )
        for assignment, result in ranked_results
    ]
        
@router.get(
    "/{committee_id}/applications/"
    "{assignment_id}/result",
    response_model=EvaluationResultRead,
)
def read_application_result(
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

    result = get_evaluation_result_by_assignment(
        db,
        assignment.id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation result not found",
        )

    return result

@router.put(
    "/{committee_id}/applications/"
    "{assignment_id}/result/decision",
    response_model=EvaluationResultRead,
)
def update_final_decision(
    committee_id: int,
    assignment_id: int,
    decision_data: EvaluationDecisionUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
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

    result = get_evaluation_result_by_assignment(
        db,
        assignment.id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Generate the committee ranking "
                "before setting a final decision"
            ),
        )

    return set_final_decision(
        db=db,
        result=result,
        decision=decision_data.decision,
        final_comment=decision_data.final_comment,
        decided_by=current_admin.id,
    )        