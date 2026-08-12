from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.evaluation_criteria.models import (
    EvaluationCriterion,
)
from app.evaluation_criteria.schemas import (
    EvaluationCriterionCreate,
    EvaluationCriterionUpdate,
)


def create_evaluation_criterion(
    db: Session,
    committee_id: int,
    criterion_data: EvaluationCriterionCreate,
    created_by: int,
) -> EvaluationCriterion:
    criterion = EvaluationCriterion(
        committee_id=committee_id,
        code=criterion_data.code,
        name=criterion_data.name,
        description=criterion_data.description,
        weight=criterion_data.weight,
        max_score=criterion_data.max_score,
        display_order=criterion_data.display_order,
        is_active=criterion_data.is_active,
        created_by=created_by,
    )

    db.add(criterion)
    db.commit()
    db.refresh(criterion)

    return criterion


def get_evaluation_criteria(
    db: Session,
    committee_id: int,
) -> list[EvaluationCriterion]:
    return (
        db.query(EvaluationCriterion)
        .filter(
            EvaluationCriterion.committee_id
            == committee_id
        )
        .order_by(
            EvaluationCriterion.display_order.asc(),
            EvaluationCriterion.id.asc(),
        )
        .all()
    )


def get_evaluation_criterion_by_id(
    db: Session,
    criterion_id: int,
) -> EvaluationCriterion | None:
    return (
        db.query(EvaluationCriterion)
        .filter(
            EvaluationCriterion.id
            == criterion_id
        )
        .first()
    )


def get_evaluation_criterion_by_code(
    db: Session,
    committee_id: int,
    code: str,
) -> EvaluationCriterion | None:
    return (
        db.query(EvaluationCriterion)
        .filter(
            EvaluationCriterion.committee_id
            == committee_id,
            EvaluationCriterion.code
            == code.strip().upper(),
        )
        .first()
    )


def get_total_active_weight(
    db: Session,
    committee_id: int,
    excluded_criterion_id: int | None = None,
) -> Decimal:
    query = (
        db.query(
            func.coalesce(
                func.sum(EvaluationCriterion.weight),
                0,
            )
        )
        .filter(
            EvaluationCriterion.committee_id
            == committee_id,
            EvaluationCriterion.is_active.is_(True),
        )
    )

    if excluded_criterion_id is not None:
        query = query.filter(
            EvaluationCriterion.id
            != excluded_criterion_id
        )

    result = query.scalar()

    return Decimal(str(result))


def update_evaluation_criterion(
    db: Session,
    criterion: EvaluationCriterion,
    criterion_data: EvaluationCriterionUpdate,
) -> EvaluationCriterion:
    update_data = criterion_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            criterion,
            field,
            value,
        )

    db.commit()
    db.refresh(criterion)

    return criterion


def delete_evaluation_criterion(
    db: Session,
    criterion: EvaluationCriterion,
) -> None:
    db.delete(criterion)
    db.commit()