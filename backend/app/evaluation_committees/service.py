from sqlalchemy.orm import Session

from app.evaluation_committees.models import (
    EvaluationCommittee,
)
from app.evaluation_committees.schemas import (
    EvaluationCommitteeCreate,
    EvaluationCommitteeUpdate,
)


def create_evaluation_committee(
    db: Session,
    committee_data: EvaluationCommitteeCreate,
    created_by: int,
) -> EvaluationCommittee:
    committee = EvaluationCommittee(
        position_id=committee_data.position_id,
        name=committee_data.name,
        description=committee_data.description,
        status="DRAFT",
        created_by=created_by,
    )

    db.add(committee)
    db.commit()
    db.refresh(committee)

    return committee


def get_evaluation_committees(
    db: Session,
) -> list[EvaluationCommittee]:
    return (
        db.query(EvaluationCommittee)
        .order_by(
            EvaluationCommittee.created_at.desc()
        )
        .all()
    )


def get_evaluation_committee_by_id(
    db: Session,
    committee_id: int,
) -> EvaluationCommittee | None:
    return (
        db.query(EvaluationCommittee)
        .filter(
            EvaluationCommittee.id == committee_id
        )
        .first()
    )


def get_evaluation_committee_by_position(
    db: Session,
    position_id: int,
) -> EvaluationCommittee | None:
    return (
        db.query(EvaluationCommittee)
        .filter(
            EvaluationCommittee.position_id
            == position_id
        )
        .first()
    )


def update_evaluation_committee(
    db: Session,
    committee: EvaluationCommittee,
    committee_data: EvaluationCommitteeUpdate,
) -> EvaluationCommittee:
    update_data = committee_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            committee,
            field,
            value,
        )

    db.commit()
    db.refresh(committee)

    return committee


def delete_evaluation_committee(
    db: Session,
    committee: EvaluationCommittee,
) -> None:
    db.delete(committee)
    db.commit()