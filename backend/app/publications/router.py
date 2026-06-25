from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.users.models import User
from app.users.router import get_current_user

from app.profiles.service import get_profile_by_user_id

from app.publications.schemas import (
    PublicationCreate,
    PublicationUpdate,
    PublicationRead,
)

from app.publications.service import (
    create_publication,
    get_publications_by_profile_id,
    get_publication_by_id,
    update_publication,
    delete_publication,
)


router = APIRouter(
    prefix="/publications",
    tags=["Publications"]
)


@router.post(
    "/",
    response_model=PublicationRead,
    status_code=status.HTTP_201_CREATED
)
def create_my_publication(
    publication_data: PublicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    return create_publication(
        db,
        profile.id,
        publication_data
    )


@router.get("/me", response_model=list[PublicationRead])
def read_my_publications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    return get_publications_by_profile_id(db, profile.id)


@router.get("/profile/{profile_id}", response_model=list[PublicationRead])
def read_publications_by_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    return get_publications_by_profile_id(db, profile_id)


@router.get("/{publication_id}", response_model=PublicationRead)
def read_publication(
    publication_id: int,
    db: Session = Depends(get_db)
):
    publication = get_publication_by_id(db, publication_id)

    if not publication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication not found"
        )

    return publication


@router.put("/{publication_id}", response_model=PublicationRead)
def update_my_publication(
    publication_id: int,
    publication_data: PublicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    publication = get_publication_by_id(db, publication_id)

    if not publication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication not found"
        )

    if publication.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update this publication"
        )

    return update_publication(
        db,
        publication,
        publication_data
    )


@router.delete("/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_publication(
    publication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    publication = get_publication_by_id(db, publication_id)

    if not publication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication not found"
        )

    if publication.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this publication"
        )

    delete_publication(db, publication)

    return None