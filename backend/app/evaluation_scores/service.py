from sqlalchemy.orm import (
    Session,
    joinedload,
)

from app.evaluation_scores.models import (
    EvaluationScore,
)
from app.evaluation_scores.schemas import (
    EvaluationScoreCreate,
    EvaluationScoreUpdate,
)


def create_evaluation_score(
    db: Session,
    committee_application_id: int,
    reviewer_id: int,
    score_data: EvaluationScoreCreate,
) -> EvaluationScore:
    evaluation_score = EvaluationScore(
        committee_application_id=(
            committee_application_id
        ),
        criterion_id=score_data.criterion_id,
        reviewer_id=reviewer_id,
        score=score_data.score,
        comment=score_data.comment,
    )

    db.add(evaluation_score)
    db.commit()
    db.refresh(evaluation_score)

    return get_evaluation_score_by_id(
        db,
        evaluation_score.id,
    )


def get_evaluation_score_by_id(
    db: Session,
    score_id: int,
) -> EvaluationScore | None:
    return (
        db.query(EvaluationScore)
        .options(
            joinedload(
                EvaluationScore.criterion
            ),
            joinedload(
                EvaluationScore.reviewer
            ),
        )
        .filter(
            EvaluationScore.id == score_id
        )
        .first()
    )


def get_existing_evaluation_score(
    db: Session,
    committee_application_id: int,
    criterion_id: int,
    reviewer_id: int,
) -> EvaluationScore | None:
    return (
        db.query(EvaluationScore)
        .filter(
            EvaluationScore.committee_application_id
            == committee_application_id,
            EvaluationScore.criterion_id
            == criterion_id,
            EvaluationScore.reviewer_id
            == reviewer_id,
        )
        .first()
    )


def get_scores_for_assignment(
    db: Session,
    committee_application_id: int,
) -> list[EvaluationScore]:
    return (
        db.query(EvaluationScore)
        .options(
            joinedload(
                EvaluationScore.criterion
            ),
            joinedload(
                EvaluationScore.reviewer
            ),
        )
        .filter(
            EvaluationScore.committee_application_id
            == committee_application_id
        )
        .order_by(
            EvaluationScore.reviewer_id.asc(),
            EvaluationScore.criterion_id.asc(),
        )
        .all()
    )


def get_reviewer_scores(
    db: Session,
    committee_application_id: int,
    reviewer_id: int,
) -> list[EvaluationScore]:
    return (
        db.query(EvaluationScore)
        .options(
            joinedload(
                EvaluationScore.criterion
            ),
            joinedload(
                EvaluationScore.reviewer
            ),
        )
        .filter(
            EvaluationScore.committee_application_id
            == committee_application_id,
            EvaluationScore.reviewer_id
            == reviewer_id,
        )
        .order_by(
            EvaluationScore.criterion_id.asc()
        )
        .all()
    )


def update_evaluation_score(
    db: Session,
    evaluation_score: EvaluationScore,
    score_data: EvaluationScoreUpdate,
) -> EvaluationScore:
    update_data = score_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            evaluation_score,
            field,
            value,
        )

    db.commit()
    db.refresh(evaluation_score)

    return get_evaluation_score_by_id(
        db,
        evaluation_score.id,
    )


def delete_evaluation_score(
    db: Session,
    evaluation_score: EvaluationScore,
) -> None:
    db.delete(evaluation_score)
    db.commit()