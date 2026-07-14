from sqlalchemy.orm import Session

from app.position_statuses.models import PositionStatus
from app.position_statuses.schemas import (
    PositionStatusCreate,
    PositionStatusUpdate,
)


def get_all_position_statuses(db: Session):
    return (
        db.query(PositionStatus)
        .order_by(PositionStatus.id.asc())
        .all()
    )


def get_position_status_by_id(
    db: Session,
    position_status_id: int,
):
    return (
        db.query(PositionStatus)
        .filter(PositionStatus.id == position_status_id)
        .first()
    )


def get_position_status_by_code(
    db: Session,
    code: str,
):
    return (
        db.query(PositionStatus)
        .filter(PositionStatus.code == code)
        .first()
    )


def create_position_status(
    db: Session,
    position_status_data: PositionStatusCreate,
):
    position_status = PositionStatus(
        **position_status_data.model_dump()
    )

    db.add(position_status)
    db.commit()
    db.refresh(position_status)

    return position_status


def update_position_status(
    db: Session,
    position_status: PositionStatus,
    position_status_data: PositionStatusUpdate,
):
    update_data = position_status_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(position_status, field, value)

    db.commit()
    db.refresh(position_status)

    return position_status


def delete_position_status(
    db: Session,
    position_status: PositionStatus,
):
    db.delete(position_status)
    db.commit()