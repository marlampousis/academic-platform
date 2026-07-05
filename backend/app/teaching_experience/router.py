from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.users.models import User
from app.users.router import get_current_user

from app.profiles.service import get_profile_by_user_id

from app.teaching_experience.schemas import (
    TeachingExperienceCreate,
    TeachingExperienceUpdate,
    TeachingExperienceRead,
)

from app.teaching_experience.service import (
    create_teaching_experience,
    get_teaching_experience_by_profile_id,
    get_teaching_experience_by_id,
    update_teaching_experience,
    delete_teaching_experience,
)


router = APIRouter(
    prefix="/teaching-experience",
    tags=["Teaching Experience"]
)


@router.post(
    "/",
    response_model=TeachingExperienceRead,
    status_code=status.HTTP_201_CREATED
)
def create_my_teaching_experience(
    teaching_data: TeachingExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    return create_teaching_experience(db, profile.id, teaching_data)


@router.get("/me", response_model=list[TeachingExperienceRead])
def read_my_teaching_experience(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    return get_teaching_experience_by_profile_id(db, profile.id)


@router.get("/profile/{profile_id}", response_model=list[TeachingExperienceRead])
def read_teaching_experience_by_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    return get_teaching_experience_by_profile_id(db, profile_id)


@router.get("/{teaching_id}", response_model=TeachingExperienceRead)
def read_teaching_experience(
    teaching_id: int,
    db: Session = Depends(get_db)
):
    teaching = get_teaching_experience_by_id(db, teaching_id)

    if not teaching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teaching experience not found"
        )

    return teaching


@router.put("/{teaching_id}", response_model=TeachingExperienceRead)
def update_my_teaching_experience(
    teaching_id: int,
    teaching_data: TeachingExperienceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    teaching = get_teaching_experience_by_id(db, teaching_id)

    if not teaching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teaching experience not found"
        )

    if teaching.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update this teaching experience"
        )

    return update_teaching_experience(db, teaching, teaching_data)


@router.delete("/{teaching_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_teaching_experience(
    teaching_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    teaching = get_teaching_experience_by_id(db, teaching_id)

    if not teaching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teaching experience not found"
        )

    if teaching.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this teaching experience"
        )

    delete_teaching_experience(db, teaching)

    return None