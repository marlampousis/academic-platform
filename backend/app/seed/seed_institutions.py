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


def seed_institutions():
    db = SessionLocal()

    try:
        for name in GREEK_UNIVERSITIES:
            existing = (
                db.query(Institution)
                .filter(Institution.name_el == name)
                .first()
            )

            if existing:
                continue

            institution = Institution(
                name_el=name,
                institution_type="UNIVERSITY",
                country="Greece",
                is_active=True
            )

            db.add(institution)

        db.commit()
        print("Greek universities seeded successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error while seeding institutions: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_institutions()