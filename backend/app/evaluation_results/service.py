from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.evaluation_reports.models import (
    EvaluationReport,
)
from app.evaluation_results.models import (
    EvaluationResult,
)

from app.committee_applications.models import (
    CommitteeApplication,
)

from app.committee_members.service import get_committee_members
from app.evaluation_reports.service import get_reports_for_assignment

def calculate_application_final_score(
    db: Session,
    committee_application_id: int,
) -> Decimal | None:
    reports = (
        db.query(EvaluationReport)
        .filter(
            EvaluationReport.committee_application_id
            == committee_application_id,
            EvaluationReport.status == "SUBMITTED",
        )
        .all()
    )

    if not reports:
        return None

    total = sum(
        Decimal(str(report.weighted_score))
        for report in reports
    )

    result = total / Decimal(len(reports))

    return result.quantize(
        Decimal("0.01")
    )


def get_evaluation_result_by_assignment(
    db: Session,
    committee_application_id: int,
) -> EvaluationResult | None:
    return (
        db.query(EvaluationResult)
        .filter(
            EvaluationResult.committee_application_id
            == committee_application_id
        )
        .first()
    )



def create_or_update_evaluation_result(
    db: Session,
    committee_application_id: int,
    final_score: Decimal,
    commit: bool = True,
) -> EvaluationResult:
    result = get_evaluation_result_by_assignment(
        db,
        committee_application_id,
    )

    if not result:
        result = EvaluationResult(
            committee_application_id=committee_application_id,
            final_score=final_score,
            decision="PENDING",
        )
        db.add(result)

    else:
        if result.decision != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Finalized evaluation results cannot be modified",
            )

        result.final_score = final_score

    if commit:
        db.commit()
        db.refresh(result)

    return result



def set_final_decision(
    db: Session,
    result: EvaluationResult,
    decision: str,
    final_comment: str | None,
    decided_by: int,
) -> EvaluationResult:
    if result.decision != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Final decision has already been recorded "
                "and cannot be overwritten"
            ),
        )
    result.decision = decision
    result.final_comment = final_comment
    result.decided_by = decided_by
    result.decided_at = datetime.utcnow()

    db.commit()
    db.refresh(result)

    return result


def validate_ranking_completeness(
    db: Session,
    committee_id: int,
    assignments: list,
) -> None:
    """
    Require one submitted report per active reviewer
    for every committee application.
    """

    members = get_committee_members(
        db=db,
        committee_id=committee_id,
    )

    active_reviewer_ids = {
        member.user_id
        for member in members
        if member.is_active
    }

    if not assignments or not active_reviewer_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ranking requires applications "
                "and active committee reviewers"
            ),
        )

    for assignment in assignments:
        reports = get_reports_for_assignment(
            db=db,
            committee_application_id=assignment.id,
        )

        submitted_ids = [
            report.reviewer_id
            for report in reports
            if (
                report.status == "SUBMITTED"
                and report.reviewer_id in active_reviewer_ids
            )
        ]

        if (
            len(submitted_ids) != len(active_reviewer_ids)
            or set(submitted_ids) != active_reviewer_ids
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot generate ranking: "
                    f"application assignment {assignment.id} "
                    "does not have all required "
                    "submitted reviewer reports"
                ),
            )


def generate_committee_ranking(
    db: Session,
    committee_id: int,
):
    assignments = (
        db.query(CommitteeApplication)
        .filter(
            CommitteeApplication.committee_id == committee_id
        )
        .all()
    )

    # Reject previously finalized decisions before changing data.
    for assignment in assignments:
        existing_result = get_evaluation_result_by_assignment(
            db,
            assignment.id,
        )

        if (
            existing_result is not None
            and existing_result.decision != "PENDING"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Ranking cannot be regenerated because "
                    "a final decision already exists"
                ),
            )

    # Verify that every required reviewer has submitted.
    validate_ranking_completeness(
        db=db,
        committee_id=committee_id,
        assignments=assignments,
    )

    # Calculate scores before modifying result records.
    calculated_scores = []

    for assignment in assignments:
        final_score = calculate_application_final_score(
            db=db,
            committee_application_id=assignment.id,
        )

        if final_score is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"No final score for assignment {assignment.id}"
                ),
            )

        calculated_scores.append(
            (assignment, final_score)
        )

    ranked_results = []

    try:
        for assignment, final_score in calculated_scores:
            result = create_or_update_evaluation_result(
                db=db,
                committee_application_id=assignment.id,
                final_score=final_score,
                commit=False,
            )

            ranked_results.append(
                (assignment, result)
            )

        ranked_results.sort(
            key=lambda item: item[1].final_score,
            reverse=True,
        )

        for index, (_, result) in enumerate(
            ranked_results,
            start=1,
        ):
            result.rank_position = index

        # Persist the entire ranking together.
        db.commit()

    except Exception:
        db.rollback()
        raise

    return ranked_results

def get_committee_ranking(
    db: Session,
    committee_id: int,
):
    """Read existing ranking records without modifying them."""

    return (
        db.query(CommitteeApplication, EvaluationResult)
        .join(
            EvaluationResult,
            EvaluationResult.committee_application_id
            == CommitteeApplication.id,
        )
        .filter(
            CommitteeApplication.committee_id
            == committee_id,
        )
        .order_by(
            EvaluationResult.rank_position.asc()
        )
        .all()
    )
