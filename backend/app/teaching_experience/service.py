from sqlalchemy.orm import Session

from app.teaching_experience.models import TeachingExperience


def create_teaching_experience(db: Session, profile_id: int, teaching_data):
    teaching = TeachingExperience(
        profile_id=profile_id,
        **teaching_data.model_dump()
    )

    db.add(teaching)
    db.commit()
    db.refresh(teaching)

    return teaching


def get_teaching_experience_by_profile_id(
    db: Session,
    profile_id: int,
    skip: int = 0,
    limit: int = 20
):
    return (
        db.query(TeachingExperience)
        .filter(TeachingExperience.profile_id == profile_id)
        .order_by(TeachingExperience.academic_year.desc().nullslast())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_teaching_experience_by_id(db: Session, teaching_id: int):
    return (
        db.query(TeachingExperience)
        .filter(TeachingExperience.id == teaching_id)
        .first()
    )


def update_teaching_experience(db: Session, teaching: TeachingExperience, teaching_data):
    update_data = teaching_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(teaching, field, value)

    db.commit()
    db.refresh(teaching)

    return teaching


def delete_teaching_experience(db: Session, teaching: TeachingExperience):
    db.delete(teaching)
    db.commit()