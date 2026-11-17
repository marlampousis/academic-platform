from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import (
    Session,
    joinedload,
)

from app.evaluation_reports.models import (
    EvaluationReport,
)
from app.evaluation_scores.models import (
    EvaluationScore,
)

from app.evaluation_criteria.models import (
    EvaluationCriterion,
)


def calculate_reviewer_weighted_score(
    db: Session,
    committee_application_id: int,
    reviewer_id: int,
) -> Decimal:
    scores = (
        db.query(EvaluationScore)
        .options(
            joinedload(EvaluationScore.criterion)
        )
        .filter(
            EvaluationScore.committee_application_id
            == committee_application_id,
            EvaluationScore.reviewer_id
            == reviewer_id,
        )
        .all()
    )

    total = Decimal("0")

    for score_record in scores:
        criterion = score_record.criterion

        if not criterion.is_active:
            continue

        weighted_value = (
            Decimal(str(score_record.score))
            / Decimal(str(criterion.max_score))
        ) * Decimal(str(criterion.weight))

        total += weighted_value

    return total.quantize(
        Decimal("0.01")
    )


def create_evaluation_report(
    db: Session,
    committee_application_id: int,
    reviewer_id: int,
    weighted_score: Decimal,
    final_comment: str | None,
) -> EvaluationReport:
    report = EvaluationReport(
        committee_application_id=(
            committee_application_id
        ),
        reviewer_id=reviewer_id,
        weighted_score=weighted_score,
        final_comment=final_comment,
        status="DRAFT",
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return get_evaluation_report_by_id(
        db,
        report.id,
    )


def get_evaluation_report_by_id(
    db: Session,
    report_id: int,
) -> EvaluationReport | None:
    return (
        db.query(EvaluationReport)
        .options(
            joinedload(
                EvaluationReport.reviewer
            )
        )
        .filter(
            EvaluationReport.id
            == report_id
        )
        .first()
    )


def get_reviewer_report(
    db: Session,
    committee_application_id: int,
    reviewer_id: int,
) -> EvaluationReport | None:
    return (
        db.query(EvaluationReport)
        .options(
            joinedload(
                EvaluationReport.reviewer
            )
        )
        .filter(
            EvaluationReport.committee_application_id
            == committee_application_id,
            EvaluationReport.reviewer_id
            == reviewer_id,
        )
        .first()
    )


def get_reports_for_assignment(
    db: Session,
    committee_application_id: int,
) -> list[EvaluationReport]:
    return (
        db.query(EvaluationReport)
        .options(
            joinedload(
                EvaluationReport.reviewer
            )
        )
        .filter(
            EvaluationReport.committee_application_id
            == committee_application_id
        )
        .order_by(
            EvaluationReport.reviewer_id.asc()
        )
        .all()
    )

def reviewer_scoring_is_complete(
    db: Session,
    committee_id: int,
    committee_application_id: int,
    reviewer_id: int,
) -> bool:
    # Retrieve the exact IDs of active committee criteria.
    active_criteria = (
        db.query(EvaluationCriterion.id)
        .filter(
            EvaluationCriterion.committee_id == committee_id,
            EvaluationCriterion.is_active.is_(True),
        )
        .all()
    )

    active_criterion_ids = {
        row[0] for row in active_criteria
    }

    if not active_criterion_ids:
        return False

    # Retrieve the IDs actually scored by this reviewer.
    reviewer_scores = (
        db.query(EvaluationScore.criterion_id)
        .filter(
            EvaluationScore.committee_application_id
            == committee_application_id,
            EvaluationScore.reviewer_id == reviewer_id,
        )
        .all()
    )

    scored_criterion_ids = [
        row[0] for row in reviewer_scores
    ]

    # Every active criterion must have exactly one score.
    # Stale or duplicate criteria must not be accepted.
    return (
        len(scored_criterion_ids) == len(active_criterion_ids)
        and set(scored_criterion_ids) == active_criterion_ids
    )

def update_evaluation_report(
    db: Session,
    report: EvaluationReport,
    final_comment: str | None,
) -> EvaluationReport:
    report.final_comment = final_comment

    db.commit()
    db.refresh(report)

    return get_evaluation_report_by_id(
        db,
        report.id,
    )

def submit_evaluation_report(
    db: Session,
    report: EvaluationReport,
) -> EvaluationReport:
    report.status = "SUBMITTED"
    report.submitted_at = datetime.utcnow()

    db.commit()
    db.refresh(report)

    return get_evaluation_report_by_id(
        db,
        report.id,
    )      