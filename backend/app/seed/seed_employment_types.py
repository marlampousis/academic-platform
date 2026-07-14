from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.employment_types.models import EmploymentType


EMPLOYMENT_TYPES = [
    {
        "code": "FULL_TIME",
        "name": "Full-time",
        "description": "Full-time employment",
    },
    {
        "code": "PART_TIME",
        "name": "Part-time",
        "description": "Part-time employment",
    },
    {
        "code": "PERMANENT",
        "name": "Permanent",
        "description": "Permanent academic employment",
    },
    {
        "code": "FIXED_TERM",
        "name": "Fixed-term",
        "description": "Fixed-term employment contract",
    },
    {
        "code": "TENURE_TRACK",
        "name": "Tenure-track",
        "description": "Tenure-track academic position",
    },
    {
        "code": "ADJUNCT",
        "name": "Adjunct",
        "description": "Adjunct academic appointment",
    },
    {
        "code": "VISITING",
        "name": "Visiting",
        "description": "Visiting academic appointment",
    },
]


def seed_employment_types(db: Session) -> dict:
    created = 0
    skipped = 0

    for employment_type_data in EMPLOYMENT_TYPES:
        existing_employment_type = (
            db.query(EmploymentType)
            .filter(
                EmploymentType.code
                == employment_type_data["code"]
            )
            .first()
        )

        if existing_employment_type:
            skipped += 1
            continue

        employment_type = EmploymentType(
            code=employment_type_data["code"],
            name=employment_type_data["name"],
            description=employment_type_data["description"],
        )

        db.add(employment_type)
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


def run_employment_types_seeder() -> None:
    db = SessionLocal()

    try:
        result = seed_employment_types(db)

        print("Employment Types seeder completed.")
        print(f"Created: {result['created']}")
        print(f"Skipped: {result['skipped']}")

    except Exception as exc:
        print(f"Employment Types seeder failed: {exc}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_employment_types_seeder()