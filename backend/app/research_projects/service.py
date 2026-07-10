from sqlalchemy.orm import Session

from app.research_projects.models import ResearchProject


def create_research_project(db: Session, profile_id: int, project_data):
    project = ResearchProject(
        profile_id=profile_id,
        **project_data.model_dump()
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


def get_research_projects_by_profile_id(
    db: Session,
    profile_id: int,
    skip: int = 0,
    limit: int = 20
):
    return (
        db.query(ResearchProject)
        .filter(ResearchProject.profile_id == profile_id)
        .order_by(ResearchProject.start_date.desc().nullslast())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_research_project_by_identifier(
    db: Session,
    profile_id: int,
    project_identifier: str
):
    return (
        db.query(ResearchProject)
        .filter(
            ResearchProject.profile_id == profile_id,
            ResearchProject.project_identifier == project_identifier
        )
        .first()
    )

def get_research_project_by_id(db: Session, project_id: int):
    return (
        db.query(ResearchProject)
        .filter(ResearchProject.id == project_id)
        .first()
    )

def get_research_project_by_title(
    db: Session,
    profile_id: int,
    title: str
):
    return (
        db.query(ResearchProject)
        .filter(
            ResearchProject.profile_id == profile_id,
            ResearchProject.title == title
        )
        .first()
    )

def update_research_project(db: Session, project: ResearchProject, project_data):
    update_data = project_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


def delete_research_project(db: Session, project: ResearchProject):
    db.delete(project)
    db.commit()