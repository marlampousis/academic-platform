from datetime import datetime
from decimal import Decimal

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
        result.final_score = final_score

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
    result.decision = decision
    result.final_comment = final_comment
    result.decided_by = decided_by
    result.decided_at = datetime.utcnow()

    db.commit()
    db.refresh(result)

    return result

def generate_committee_ranking(
    db: Session,
    committee_id: int,
):
    assignments = (
        db.query(CommitteeApplication)
        .filter(
            CommitteeApplication.committee_id
            == committee_id
        )
        .all()
    )

    ranked_results = []

    for assignment in assignments:
        final_score = calculate_application_final_score(
            db=db,
            committee_application_id=assignment.id,
        )

        if final_score is None:
            continue

        result = create_or_update_evaluation_result(
            db=db,
            committee_application_id=assignment.id,
            final_score=final_score,
        )

        ranked_results.append(
            (
                assignment,
                result,
            )
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

    db.commit()

    return ranked_results