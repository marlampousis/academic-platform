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
from app.evaluation_reports.schemas import (
    EvaluationReportCreate,
    EvaluationReportRead,
    EvaluationReportUpdate,
)
from app.evaluation_reports.service import (
    calculate_reviewer_weighted_score,
    create_evaluation_report,
    get_evaluation_report_by_id,
    get_reports_for_assignment,
    get_reviewer_report,
    reviewer_scoring_is_complete,
    submit_evaluation_report,
    update_evaluation_report,
)
from app.users.models import User


router = APIRouter(
    prefix="/evaluation-committees",
    tags=["Evaluation Reports"],
)

def validate_report_reviewer(
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
    "{assignment_id}/reports",
    response_model=EvaluationReportRead,
    status_code=status.HTTP_201_CREATED,
)
def create_my_evaluation_report(
    committee_id: int,
    assignment_id: int,
    report_data: EvaluationReportCreate,
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
                "Evaluation reports can only be created "
                "for active committees"
            ),
        )

    validate_report_reviewer(
        db=db,
        committee_id=committee_id,
        reviewer_id=current_reviewer.id,
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

    if assignment.status != "IN_EVALUATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Evaluation reports can only be created "
                "while the application is IN_EVALUATION"
            ),
        )

    existing_report = get_reviewer_report(
        db=db,
        committee_application_id=assignment.id,
        reviewer_id=current_reviewer.id,
    )

    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Reviewer already has an evaluation "
                "report for this application"
            ),
        )

    scoring_complete = reviewer_scoring_is_complete(
        db=db,
        committee_id=committee_id,
        committee_application_id=assignment.id,
        reviewer_id=current_reviewer.id,
    )

    if not scoring_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Reviewer must score all active criteria "
                "before creating an evaluation report"
            ),
        )

    weighted_score = calculate_reviewer_weighted_score(
        db=db,
        committee_application_id=assignment.id,
        reviewer_id=current_reviewer.id,
    )

    return create_evaluation_report(
        db=db,
        committee_application_id=assignment.id,
        reviewer_id=current_reviewer.id,
        weighted_score=weighted_score,
        final_comment=report_data.final_comment,
    )
    
@router.get(
    "/{committee_id}/applications/"
    "{assignment_id}/reports/me",
    response_model=EvaluationReportRead,
)
def read_my_evaluation_report(
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

    validate_report_reviewer(
        db=db,
        committee_id=committee_id,
        reviewer_id=current_reviewer.id,
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

    report = get_reviewer_report(
        db=db,
        committee_application_id=assignment.id,
        reviewer_id=current_reviewer.id,
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation report not found",
        )

    return report    

@router.put(
    "/{committee_id}/applications/"
    "{assignment_id}/reports/{report_id}",
    response_model=EvaluationReportRead,
)
def edit_my_evaluation_report(
    committee_id: int,
    assignment_id: int,
    report_id: int,
    report_data: EvaluationReportUpdate,
    db: Session = Depends(get_db),
    current_reviewer: User = Depends(
        require_roles("REVIEWER")
    ),
):
    validate_report_reviewer(
        db=db,
        committee_id=committee_id,
        reviewer_id=current_reviewer.id,
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

    report = get_evaluation_report_by_id(
        db,
        report_id,
    )

    if (
        not report
        or report.committee_application_id != assignment.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation report not found",
        )

    if report.reviewer_id != current_reviewer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Reviewers can only modify "
                "their own evaluation reports"
            ),
        )

    if report.status == "SUBMITTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Submitted evaluation reports "
                "cannot be modified"
            ),
        )

    return update_evaluation_report(
        db=db,
        report=report,
        final_comment=report_data.final_comment,
    )
    
@router.post(
    "/{committee_id}/applications/"
    "{assignment_id}/reports/{report_id}/submit",
    response_model=EvaluationReportRead,
)
def submit_my_evaluation_report(
    committee_id: int,
    assignment_id: int,
    report_id: int,
    db: Session = Depends(get_db),
    current_reviewer: User = Depends(
        require_roles("REVIEWER")
    ),
):
    validate_report_reviewer(
        db=db,
        committee_id=committee_id,
        reviewer_id=current_reviewer.id,
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

    report = get_evaluation_report_by_id(
        db,
        report_id,
    )

    if (
        not report
        or report.committee_application_id != assignment.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation report not found",
        )

    if report.reviewer_id != current_reviewer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Reviewers can only submit "
                "their own evaluation reports"
            ),
        )

    if report.status == "SUBMITTED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evaluation report is already submitted",
        )

    return submit_evaluation_report(
        db=db,
        report=report,
    )
    
@router.get(
    "/{committee_id}/applications/"
    "{assignment_id}/reports",
    response_model=list[EvaluationReportRead],
)
def read_all_evaluation_reports(
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

    return get_reports_for_assignment(
        db=db,
        committee_application_id=assignment.id,
    )        