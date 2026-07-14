from sqlalchemy.orm import Session

from app.academic_ranks.models import AcademicRank
from app.academic_ranks.schemas import (
    AcademicRankCreate,
    AcademicRankUpdate,
)


def get_all_academic_ranks(db: Session):
    return db.query(AcademicRank).order_by(AcademicRank.level).all()


def get_academic_rank(rank_id: int, db: Session):
    return (
        db.query(AcademicRank)
        .filter(AcademicRank.id == rank_id)
        .first()
    )


def create_academic_rank(
    rank: AcademicRankCreate,
    db: Session,
):
    academic_rank = AcademicRank(**rank.model_dump())

    db.add(academic_rank)
    db.commit()
    db.refresh(academic_rank)

    return academic_rank


def update_academic_rank(
    rank_id: int,
    rank: AcademicRankUpdate,
    db: Session,
):
    academic_rank = get_academic_rank(rank_id, db)

    if not academic_rank:
        return None

    update_data = rank.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(academic_rank, key, value)

    db.commit()
    db.refresh(academic_rank)

    return academic_rank


def delete_academic_rank(
    rank_id: int,
    db: Session,
):
    academic_rank = get_academic_rank(rank_id, db)

    if not academic_rank:
        return None

    db.delete(academic_rank)
    db.commit()

    return academic_rank