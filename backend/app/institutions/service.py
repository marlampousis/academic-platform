from sqlalchemy.orm import Session

from app.institutions.models import Institution


def get_institutions(db: Session):
    return db.query(Institution).order_by(Institution.name_el).all()


def get_institution_by_id(db: Session, institution_id: int):
    return db.query(Institution).filter(Institution.id == institution_id).first()