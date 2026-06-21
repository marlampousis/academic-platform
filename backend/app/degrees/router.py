from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.users.models import User
from app.users.router import get_current_user

from app.profiles.service import get_profile_by_user_id

from app.degrees.schemas import DegreeCreate, DegreeRead
from app.degrees.service import (
    create_degree,
    get_degrees_by_profile_id,
    get_degree_by_id,
    delete_degree
)


router = APIRouter(
    prefix="/degrees",
    tags=["Degrees"]
)


@router.post(
    "/",
    response_model=DegreeRead,
    status_code=status.HTTP_201_CREATED
)
def create_my_degree(
    degree_data: DegreeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    return create_degree(
        db,
        profile.id,
        degree_data
    )


@router.get("/me", response_model=list[DegreeRead])
def read_my_degrees(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    return get_degrees_by_profile_id(db, profile.id)


@router.get("/profile/{profile_id}", response_model=list[DegreeRead])
def read_degrees_by_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    return get_degrees_by_profile_id(db, profile_id)


@router.delete("/{degree_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_degree(
    degree_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    degree = get_degree_by_id(db, degree_id)

    if not degree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Degree not found"
        )

    if degree.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this degree"
        )

    delete_degree(db, degree)

    return None