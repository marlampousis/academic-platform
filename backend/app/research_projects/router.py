from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.users.models import User
from app.users.router import get_current_user

from app.profiles.service import get_profile_by_user_id

from app.research_projects.schemas import (
    ResearchProjectCreate,
    ResearchProjectUpdate,
    ResearchProjectRead,
)

from app.research_projects.service import (
    create_research_project,
    get_research_projects_by_profile_id,
    get_research_project_by_id,
    update_research_project,
    delete_research_project,
    get_research_project_by_identifier
)


router = APIRouter(
    prefix="/research-projects",
    tags=["Research Projects"]
)


@router.post(
    "/",
    response_model=ResearchProjectRead,
    status_code=status.HTTP_201_CREATED
)
def create_my_research_project(
    project_data: ResearchProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    if project_data.project_identifier:
        existing_project = get_research_project_by_identifier(
            db,
            profile.id,
            project_data.project_identifier
        )

        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Research project with this identifier already exists"
            )
    return create_research_project(
        db,
        profile.id,
        project_data
    )


@router.get("/me", response_model=list[ResearchProjectRead])
def read_my_research_projects(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    return get_research_projects_by_profile_id(db, profile.id, skip, limit)


@router.get("/profile/{profile_id}", response_model=list[ResearchProjectRead])
def read_research_projects_by_profile(
    profile_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return get_research_projects_by_profile_id(db, profile_id, skip, limit)


@router.get("/{project_id}", response_model=ResearchProjectRead)
def read_research_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = get_research_project_by_id(db, project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found"
        )

    return project


@router.put("/{project_id}", response_model=ResearchProjectRead)
def update_my_research_project(
    project_id: int,
    project_data: ResearchProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    project = get_research_project_by_id(db, project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found"
        )

    if project.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update this research project"
        )

    return update_research_project(
        db,
        project,
        project_data
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_research_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    project = get_research_project_by_id(db, project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found"
        )

    if project.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this research project"
        )

    delete_research_project(db, project)

    return None