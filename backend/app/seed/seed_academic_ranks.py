from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.academic_ranks.models import AcademicRank


ACADEMIC_RANKS = [
    {
        "name": "Postdoctoral Researcher",
        "level": 1,
        "description": "Postdoctoral Researcher",
    },
    {
        "name": "Research Fellow",
        "level": 2,
        "description": "Research Fellow",
    },
    {
        "name": "Lecturer",
        "level": 3,
        "description": "Lecturer",
    },
    {
        "name": "Assistant Professor",
        "level": 4,
        "description": "Assistant Professor",
    },
    {
        "name": "Associate Professor",
        "level": 5,
        "description": "Associate Professor",
    },
    {
        "name": "Professor",
        "level": 6,
        "description": "Full Professor",
    },
]


def seed_academic_ranks(db: Session) -> dict:
    created = 0
    skipped = 0

    for rank_data in ACADEMIC_RANKS:

        existing_rank = (
            db.query(AcademicRank)
            .filter(
                AcademicRank.name == rank_data["name"]
            )
            .first()
        )

        if existing_rank:
            skipped += 1
            continue

        academic_rank = AcademicRank(
            name=rank_data["name"],
            level=rank_data["level"],
            description=rank_data["description"],
        )

        db.add(academic_rank)
        created += 1

    db.commit()

    return {
        "created": created,
        "skipped": skipped,
    }


def run_academic_ranks_seeder():
    db = SessionLocal()

    try:
        result = seed_academic_ranks(db)

        print("Academic Ranks seeder completed.")
        print(f"Created: {result['created']}")
        print(f"Skipped: {result['skipped']}")

    except Exception as exc:
        db.rollback()
        print(f"Academic Ranks seeder failed: {exc}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_academic_ranks_seeder()