from sqlalchemy.orm import Session

from app.publications.models import Publication


def create_publication(db: Session, profile_id: int, publication_data):
    publication = Publication(
        profile_id=profile_id,
        **publication_data.model_dump()
    )

    db.add(publication)
    db.commit()
    db.refresh(publication)

    return publication


def get_publications_by_profile_id(db: Session, profile_id: int):
    return (
        db.query(Publication)
        .filter(Publication.profile_id == profile_id)
        .order_by(Publication.publication_year.desc().nullslast())
        .all()
    )


def get_publication_by_id(db: Session, publication_id: int):
    return (
        db.query(Publication)
        .filter(Publication.id == publication_id)
        .first()
    )


def update_publication(db: Session, publication: Publication, publication_data):
    update_data = publication_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(publication, field, value)

    db.commit()
    db.refresh(publication)

    return publication


def delete_publication(db: Session, publication: Publication):
    db.delete(publication)
    db.commit()