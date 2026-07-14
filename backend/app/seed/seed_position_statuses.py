from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.position_statuses.models import PositionStatus


POSITION_STATUSES = [
    {
        "code": "DRAFT",
        "name": "Draft",
        "description": "Position is being prepared and is not publicly available",
    },
    {
        "code": "OPEN",
        "name": "Open",
        "description": "Position is open for applications",
    },
    {
        "code": "CLOSED",
        "name": "Closed",
        "description": "Position is no longer accepting applications",
    },
    {
        "code": "CANCELLED",
        "name": "Cancelled",
        "description": "Position has been cancelled",
    },
]


def seed_position_statuses(db: Session) -> dict:
    created = 0
    skipped = 0

    for status_data in POSITION_STATUSES:
        existing_status = (
            db.query(PositionStatus)
            .filter(
                PositionStatus.code == status_data["code"]
            )
            .first()
        )

        if existing_status:
            skipped += 1
            continue

        position_status = PositionStatus(
            code=status_data["code"],
            name=status_data["name"],
            description=status_data["description"],
        )

        db.add(position_status)
        created += 1

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "created": created,
        "skipped": skipped,
    }


def run_position_statuses_seeder() -> None:
    db = SessionLocal()

    try:
        result = seed_position_statuses(db)

        print("Position Statuses seeder completed.")
        print(f"Created: {result['created']}")
        print(f"Skipped: {result['skipped']}")

    except Exception as exc:
        print(f"Position Statuses seeder failed: {exc}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_position_statuses_seeder()