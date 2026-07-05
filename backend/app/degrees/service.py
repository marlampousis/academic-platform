from sqlalchemy.orm import Session

from app.degrees.models import Degree


def create_degree(db: Session, profile_id: int, degree_data):
    degree = Degree(
        profile_id=profile_id,
        **degree_data.model_dump()
    )

    db.add(degree)
    db.commit()
    db.refresh(degree)

    return degree

def get_duplicate_degree(
    db: Session,
    profile_id: int,
    degree_type: str,
    title: str,
    institution_name: str,
    end_year: int | None
):
    return (
        db.query(Degree)
        .filter(
            Degree.profile_id == profile_id,
            Degree.degree_type == degree_type,
            Degree.title == title,
            Degree.institution_name == institution_name,
            Degree.end_year == end_year
        )
        .first()
    )

def get_degrees_by_profile_id(
    db: Session,
    profile_id: int,
    skip: int = 0,
    limit: int = 20
):
    return (
        db.query(Degree)
        .filter(Degree.profile_id == profile_id)
        .order_by(Degree.end_year.desc().nullslast())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_degree_by_id(db: Session, degree_id: int):
    return (
        db.query(Degree)
        .filter(Degree.id == degree_id)
        .first()
    )


def delete_degree(db: Session, degree: Degree):
    db.delete(degree)
    db.commit()