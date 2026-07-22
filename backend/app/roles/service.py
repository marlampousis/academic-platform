from sqlalchemy.orm import Session

from app.roles.models import Role


def get_roles(db: Session) -> list[Role]:
    return (
        db.query(Role)
        .order_by(Role.id)
        .all()
    )


def get_role_by_id(
    db: Session,
    role_id: int,
) -> Role | None:
    return (
        db.query(Role)
        .filter(Role.id == role_id)
        .first()
    )


def get_role_by_code(
    db: Session,
    code: str,
) -> Role | None:
    normalized_code = code.strip().upper()

    return (
        db.query(Role)
        .filter(Role.code == normalized_code)
        .first()
    )