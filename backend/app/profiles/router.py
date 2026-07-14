from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.users.models import User
from app.users.router import get_current_user

from app.profiles.schemas import (
    AcademicProfileCreate,
    AcademicProfileRead,
    AcademicProfileUpdate
)

from app.profiles.service import (
    create_profile,
    get_profile_by_user_id,
    get_profile_by_id,
    update_profile
)

from app.academic_ranks.models import AcademicRank

router = APIRouter(
    prefix="/profiles",
    tags=["Academic Profiles"]
)

@router.post(
    "/",
    response_model=AcademicProfileRead,
    status_code=status.HTTP_201_CREATED
)
def create_my_profile(
    profile_data: AcademicProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    existing_profile = get_profile_by_user_id(
        db,
        current_user.id
    )

    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Profile already exists"
        )

    if profile_data.academic_rank_id is not None:
        academic_rank = (
            db.query(AcademicRank)
            .filter(
                AcademicRank.id == profile_data.academic_rank_id
            )
            .first()
        )

        if not academic_rank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic rank not found",
            )
    return create_profile(
        db,
        current_user.id,
        profile_data
    )
    
@router.get("/me", response_model=AcademicProfileRead)
def read_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    return profile


@router.put("/me", response_model=AcademicProfileRead)
def update_my_profile(
    profile_data: AcademicProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    return update_profile(db, profile, profile_data)


@router.get("/{profile_id}", response_model=AcademicProfileRead)
def read_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    profile = get_profile_by_id(db, profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    return profile