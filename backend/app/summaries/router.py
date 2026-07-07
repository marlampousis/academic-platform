from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.users.models import User
from app.users.router import get_current_user

from app.summaries.service import (
    get_research_summary_by_profile_id,
    get_research_summary_by_user_id,
)


router = APIRouter(
    prefix="/summaries",
    tags=["Research Summaries"]
)


@router.get("/me")
def read_my_research_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    summary = get_research_summary_by_user_id(db, current_user.id)

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    return summary


@router.get("/profile/{profile_id}")
def read_profile_research_summary(
    profile_id: int,
    db: Session = Depends(get_db)
):
    summary = get_research_summary_by_profile_id(db, profile_id)

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    return summary