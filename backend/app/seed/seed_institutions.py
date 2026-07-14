from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.institutions.models import Institution


GREEK_UNIVERSITIES = [
    "Εθνικό και Καποδιστριακό Πανεπιστήμιο Αθηνών",
    "Εθνικό Μετσόβιο Πολυτεχνείο",
    "Αριστοτέλειο Πανεπιστήμιο Θεσσαλονίκης",
    "Οικονομικό Πανεπιστήμιο Αθηνών",
    "Γεωπονικό Πανεπιστήμιο Αθηνών",
    "Ανώτατη Σχολή Καλών Τεχνών",
    "Πάντειο Πανεπιστήμιο Κοινωνικών και Πολιτικών Επιστημών",
    "Πανεπιστήμιο Πειραιώς",
    "Πανεπιστήμιο Μακεδονίας",
    "Πανεπιστήμιο Πατρών",
    "Πανεπιστήμιο Ιωαννίνων",
    "Δημοκρίτειο Πανεπιστήμιο Θράκης",
    "Πανεπιστήμιο Κρήτης",
    "Πολυτεχνείο Κρήτης",
    "Πανεπιστήμιο Αιγαίου",
    "Ιόνιο Πανεπιστήμιο",
    "Πανεπιστήμιο Θεσσαλίας",
    "Χαροκόπειο Πανεπιστήμιο",
    "Πανεπιστήμιο Πελοποννήσου",
    "Πανεπιστήμιο Δυτικής Μακεδονίας",
    "Ελληνικό Ανοικτό Πανεπιστήμιο",
    "Διεθνές Πανεπιστήμιο της Ελλάδος",
    "Πανεπιστήμιο Δυτικής Αττικής",
    "Ελληνικό Μεσογειακό Πανεπιστήμιο",
]


def seed_institutions(db: Session) -> dict:
    created = 0
    skipped = 0

    for institution_name in GREEK_UNIVERSITIES:
        existing_institution = (
            db.query(Institution)
            .filter(Institution.name_el == institution_name)
            .first()
        )

        if existing_institution:
            skipped += 1
            continue

        institution = Institution(
            name_el=institution_name,
            name_en=None,
        )

        db.add(institution)
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


def run_institutions_seeder() -> None:
    db = SessionLocal()

    try:
        result = seed_institutions(db)

        print("Institutions seeder completed.")
        print(f"Created: {result['created']}")
        print(f"Skipped: {result['skipped']}")

    except Exception as exc:
        print(f"Institutions seeder failed: {exc}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_institutions_seeder()