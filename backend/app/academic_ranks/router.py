from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.academic_ranks.schemas import (
    AcademicRankCreate,
    AcademicRankUpdate,
    AcademicRankResponse,
)

from app.academic_ranks.service import (
    get_all_academic_ranks,
    get_academic_rank,
    create_academic_rank,
    update_academic_rank,
    delete_academic_rank,
)

router = APIRouter(
    prefix="/academic-ranks",
    tags=["Academic Ranks"],
)


@router.get(
    "/",
    response_model=List[AcademicRankResponse],
)
def get_ranks(
    db: Session = Depends(get_db),
):
    return get_all_academic_ranks(db)


@router.get(
    "/{rank_id}",
    response_model=AcademicRankResponse,
)
def get_rank(
    rank_id: int,
    db: Session = Depends(get_db),
):
    academic_rank = get_academic_rank(rank_id, db)

    if not academic_rank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic rank not found",
        )

    return academic_rank


@router.post(
    "/",
    response_model=AcademicRankResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rank(
    rank: AcademicRankCreate,
    db: Session = Depends(get_db),
):
    return create_academic_rank(rank, db)


@router.put(
    "/{rank_id}",
    response_model=AcademicRankResponse,
)
def update_rank(
    rank_id: int,
    rank: AcademicRankUpdate,
    db: Session = Depends(get_db),
):
    academic_rank = update_academic_rank(
        rank_id,
        rank,
        db,
    )

    if not academic_rank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic rank not found",
        )

    return academic_rank


@router.delete(
    "/{rank_id}",
)
def delete_rank(
    rank_id: int,
    db: Session = Depends(get_db),
):
    academic_rank = delete_academic_rank(
        rank_id,
        db,
    )

    if not academic_rank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic rank not found",
        )

    return {
        "message": "Academic rank deleted successfully"
    }