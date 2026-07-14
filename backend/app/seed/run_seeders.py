from app.core.database import SessionLocal

from app.seed.seed_institutions import seed_institutions
from app.seed.seed_departments import seed_departments
from app.seed.seed_academic_ranks import seed_academic_ranks
from app.seed.seed_employment_types import seed_employment_types
from app.seed.seed_position_statuses import seed_position_statuses
from app.seed.seed_document_types import seed_document_types


def print_result(name: str, result: dict) -> None:
    print(f"\n{name}")
    print("-" * len(name))

    if "dataset_records" in result:
        print(f"Dataset records: {result['dataset_records']}")

    print(f"Created: {result.get('created', 0)}")
    print(f"Skipped: {result.get('skipped', 0)}")

    missing_institutions = result.get("missing_institutions", [])

    if missing_institutions:
        print("Missing institutions:")

        for institution_name in missing_institutions:
            print(f"- {institution_name}")


def run_all_seeders() -> None:
    db = SessionLocal()

    try:
        print("Starting application seeders...")

        institutions_result = seed_institutions(db)
        print_result(
            "Institutions Seeder",
            institutions_result,
        )

        departments_result = seed_departments(db)
        print_result(
            "Departments Seeder",
            departments_result,
        )

        academic_ranks_result = seed_academic_ranks(db)
        print_result(
            "Academic Ranks Seeder",
            academic_ranks_result,
        )

        employment_types_result = seed_employment_types(db)
        print_result(
            "Employment Types Seeder",
            employment_types_result,
        )

        position_statuses_result = seed_position_statuses(db)
        print_result(
            "Position Statuses Seeder",
            position_statuses_result,
        )

        document_types_result = seed_document_types(db)
        print_result(
            "Document Types Seeder",
            document_types_result,
        )

        print("\nAll seeders completed successfully.")

    except Exception as exc:
        db.rollback()

        print("\nSeeder execution failed.")
        print(f"Error: {exc}")

        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_all_seeders()