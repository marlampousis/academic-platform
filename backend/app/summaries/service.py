from sqlalchemy.orm import Session

from app.profiles.service import get_profile_by_id, get_profile_by_user_id
from app.metrics.service import get_profile_metrics

from app.degrees.service import get_degrees_by_profile_id
from app.publications.service import get_publications_by_profile_id
from app.research_projects.service import get_research_projects_by_profile_id
from app.teaching_experience.service import get_teaching_experience_by_profile_id


def get_research_summary_by_profile_id(db: Session, profile_id: int):
    profile = get_profile_by_id(db, profile_id)

    if not profile:
        return None

    return {
        "profile": profile,
        "metrics": get_profile_metrics(db, profile_id),
        "degrees": get_degrees_by_profile_id(db, profile_id, skip=0, limit=100),
        "publications": get_publications_by_profile_id(db, profile_id, skip=0, limit=100),
        "research_projects": get_research_projects_by_profile_id(db, profile_id, skip=0, limit=100),
        "teaching_experience": get_teaching_experience_by_profile_id(db, profile_id, skip=0, limit=100),
    }


def get_research_summary_by_user_id(db: Session, user_id: int):
    profile = get_profile_by_user_id(db, user_id)

    if not profile:
        return None

    return get_research_summary_by_profile_id(db, profile.id)