from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.users.models import User
from app.users.router import get_current_user

from app.profiles.service import (
    get_profile_by_user_id,
    get_profile_by_id
)

from app.metrics.schemas import ProfileMetricsRead
from app.metrics.service import get_profile_metrics


router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"]
)


@router.get("/me", response_model=ProfileMetricsRead)
def read_my_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    return get_profile_metrics(db, profile.id)


@router.get("/profile/{profile_id}", response_model=ProfileMetricsRead)
def read_profile_metrics(
    profile_id: int,
    db: Session = Depends(get_db)
):
    profile = get_profile_by_id(db, profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    return get_profile_metrics(db, profile.id)