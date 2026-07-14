from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.document_types.models import DocumentType


DOCUMENT_TYPES = [
    {
        "code": "CV",
        "name": "Curriculum Vitae",
        "description": "Academic curriculum vitae",
        "is_active": True,
    },
    {
        "code": "BACHELOR_DEGREE",
        "name": "Bachelor Degree",
        "description": "Bachelor degree certificate",
        "is_active": True,
    },
    {
        "code": "MASTER_DEGREE",
        "name": "Master Degree",
        "description": "Master degree certificate",
        "is_active": True,
    },
    {
        "code": "PHD_DEGREE",
        "name": "PhD Degree",
        "description": "Doctoral degree certificate",
        "is_active": True,
    },
    {
        "code": "TEACHING_CERTIFICATE",
        "name": "Teaching Certificate",
        "description": "Certificate of teaching experience",
        "is_active": True,
    },
    {
        "code": "EMPLOYMENT_CERTIFICATE",
        "name": "Employment Certificate",
        "description": "Certificate of professional or academic employment",
        "is_active": True,
    },
    {
        "code": "LANGUAGE_CERTIFICATE",
        "name": "Language Certificate",
        "description": "Foreign language proficiency certificate",
        "is_active": True,
    },
    {
        "code": "RESEARCH_STATEMENT",
        "name": "Research Statement",
        "description": "Applicant research statement",
        "is_active": True,
    },
    {
        "code": "TEACHING_STATEMENT",
        "name": "Teaching Statement",
        "description": "Applicant teaching statement",
        "is_active": True,
    },
    {
        "code": "COVER_LETTER",
        "name": "Cover Letter",
        "description": "Application cover letter",
        "is_active": True,
    },
    {
        "code": "RECOMMENDATION_LETTER",
        "name": "Recommendation Letter",
        "description": "Academic recommendation letter",
        "is_active": True,
    },
    {
        "code": "PUBLICATION_LIST",
        "name": "Publication List",
        "description": "Complete list of academic publications",
        "is_active": True,
    },
    {
        "code": "IDENTITY_DOCUMENT",
        "name": "Identity Document",
        "description": "National identity card or passport",
        "is_active": True,
    },
    {
        "code": "DECLARATION",
        "name": "Declaration",
        "description": "Formal applicant declaration",
        "is_active": True,
    },
    {
        "code": "OTHER",
        "name": "Other Document",
        "description": "Other supporting document",
        "is_active": True,
    },
]


def seed_document_types(db: Session) -> dict:
    created = 0
    skipped = 0

    for document_type_data in DOCUMENT_TYPES:
        existing_document_type = (
            db.query(DocumentType)
            .filter(
                DocumentType.code
                == document_type_data["code"]
            )
            .first()
        )

        if existing_document_type:
            skipped += 1
            continue

        document_type = DocumentType(
            code=document_type_data["code"],
            name=document_type_data["name"],
            description=document_type_data["description"],
            is_active=document_type_data["is_active"],
        )

        db.add(document_type)
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


def run_document_types_seeder() -> None:
    db = SessionLocal()

    try:
        result = seed_document_types(db)

        print("Document Types seeder completed.")
        print(f"Created: {result['created']}")
        print(f"Skipped: {result['skipped']}")

    except Exception as exc:
        print(f"Document Types seeder failed: {exc}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_document_types_seeder()