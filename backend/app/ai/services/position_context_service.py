
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.academic_positions.models import AcademicPosition


class PositionNotFound(Exception):
    """Academic position does not exist."""


class PositionContextError(Exception):
    """Academic position has insufficient information."""


@dataclass(frozen=True)
class PositionContext:
    position_id: int
    title: str
    field_of_study: str
    description: str


def get_position_context(
    db: Session,
    *,
    position_id: int,
) -> PositionContext:

    if position_id <= 0:
        raise ValueError("Position ID must be positive")

    position = db.get(
        AcademicPosition,
        position_id,
    )

    if position is None:
        raise PositionNotFound(
            f"Academic position {position_id} not found"
        )

    title = (position.title or "").strip()
    description = (position.description or "").strip()
    field_of_study = (
        position.field_of_study or ""
    ).strip()

    if not title or not description:
        raise PositionContextError(
            "Academic position has no valid "
            "title or description"
        )

    return PositionContext(
        position_id=position.id,
        title=title,
        field_of_study=field_of_study,
        description=description,
    )
