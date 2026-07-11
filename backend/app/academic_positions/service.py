from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.academic_positions.models import AcademicPosition
from app.academic_positions.schemas import (
    AcademicPositionCreate,
    AcademicPositionUpdate,
)


def create_position(
    db: Session,
    user_id: int,
    position_data: AcademicPositionCreate,
):
    position = AcademicPosition(
        created_by=user_id,
        **position_data.model_dump(),
    )

    try:
        db.add(position)
        db.commit()
        db.refresh(position)

        return position

    except SQLAlchemyError:
        db.rollback()
        raise


def get_positions(
    db: Session,
):
    return (
        db.query(AcademicPosition)
        .order_by(AcademicPosition.created_at.desc())
        .all()
    )


def get_position_by_id(
    db: Session,
    position_id: int,
):
    return (
        db.query(AcademicPosition)
        .filter(AcademicPosition.id == position_id)
        .first()
    )


def update_position(
    db: Session,
    position: AcademicPosition,
    position_data: AcademicPositionUpdate,
):
    update_data = position_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(position, field, value)

    db.commit()
    db.refresh(position)

    return position


def delete_position(
    db: Session,
    position: AcademicPosition,
):
    db.delete(position)
    db.commit()