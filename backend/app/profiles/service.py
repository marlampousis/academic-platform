from sqlalchemy.orm import Session

from app.profiles.models import AcademicProfile


def get_profile_by_user_id(
    db: Session,
    user_id: int
):
    return (
        db.query(AcademicProfile)
        .filter(AcademicProfile.user_id == user_id)
        .first()
    )
    
def create_profile(
    db: Session,
    user_id: int,
    profile_data
):
    profile = AcademicProfile(
        user_id=user_id,
        **profile_data.model_dump()
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile

def get_profile_by_id(db: Session, profile_id: int):
    return (
        db.query(AcademicProfile)
        .filter(AcademicProfile.id == profile_id)
        .first()
    )


def update_profile(db: Session, profile: AcademicProfile, profile_data):
    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile