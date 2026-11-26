
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.profiles.models import AcademicProfile
from app.degrees.models import Degree
from app.publications.models import Publication
from app.research_projects.models import ResearchProject
from app.teaching_experience.models import TeachingExperience

from app.ai.schemas.candidate_context import (
    CandidateAcademicContext,
    DegreeEvidence,
    PublicationEvidence,
    ResearchProjectEvidence,
    TeachingEvidence,
)


class CandidateProfileNotFound(Exception):
    """The requested academic profile is unavailable."""


class CandidateProfileAccessDenied(Exception):
    """The profile does not belong to the expected user."""


def get_candidate_academic_context(
    db: Session,
    *,
    profile_id: int,
    expected_user_id: int,
) -> CandidateAcademicContext:

    if profile_id <= 0 or expected_user_id <= 0:
        raise ValueError(
            "Profile ID and user ID must be positive"
        )

    profile = db.get(AcademicProfile, profile_id)

    if profile is None:
        raise CandidateProfileNotFound(
            "Academic profile not found"
        )

    if profile.user_id != expected_user_id:
        raise CandidateProfileAccessDenied(
            "Academic profile ownership mismatch"
        )

    degrees = db.scalars(
        select(Degree)
        .where(Degree.profile_id == profile_id)
        .order_by(Degree.id)
    ).all()

    publications = db.scalars(
        select(Publication)
        .where(Publication.profile_id == profile_id)
        .order_by(Publication.id)
    ).all()

    projects = db.scalars(
        select(ResearchProject)
        .where(ResearchProject.profile_id == profile_id)
        .order_by(ResearchProject.id)
    ).all()

    teaching = db.scalars(
        select(TeachingExperience)
        .where(TeachingExperience.profile_id == profile_id)
        .order_by(TeachingExperience.id)
    ).all()

    return CandidateAcademicContext(
        profile_id=profile.id,
        user_id=profile.user_id,
        specialization=profile.specialization,
        research_areas=profile.research_areas,

        degrees=[
            DegreeEvidence.model_validate({
                "id": item.id,
                "degree_type": item.degree_type,
                "title": item.title,
                "field_of_study": item.field_of_study,
                "institution_name": item.institution_name,
                "start_year": item.start_year,
                "end_year": item.end_year,
            })
            for item in degrees
        ],

        publications=[
            PublicationEvidence.model_validate({
                "id": item.id,
                "title": item.title,
                "publication_year": item.publication_year,
                "publication_type": item.publication_type,
                "doi": item.doi,
                "journal_name": item.journal_name,
            })
            for item in publications
        ],

        research_projects=[
            ResearchProjectEvidence.model_validate({
                "id": item.id,
                "title": item.title,
                "role": item.role,
                "status": item.status,
                "start_date": item.start_date,
                "end_date": item.end_date,
                "description": item.description,
            })
            for item in projects
        ],

        teaching_experience=[
            TeachingEvidence.model_validate({
                "id": item.id,
                "course_title": item.course_title,
                "institution_name": item.institution_name,
                "academic_year": item.academic_year,
                "teaching_role": item.teaching_role,
                "hours_per_week": item.hours_per_week,
            })
            for item in teaching
        ],
    )
