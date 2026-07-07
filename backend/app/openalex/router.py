from fastapi import APIRouter, HTTPException, Query, status, Depends

from app.openalex.client import search_works, get_work_by_doi
from app.openalex.schemas import OpenAlexWorkPreview

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.users.models import User
from app.users.router import get_current_user
from app.profiles.service import get_profile_by_user_id

from app.publications.schemas import PublicationCreate, PublicationRead
from app.publications.service import (
    create_publication,
    get_publication_by_doi,
)

from app.openalex.schemas import (
    OpenAlexWorkPreview,
    OpenAlexImportRequest,
)

from app.openalex.client import (
    search_works,
    get_work_by_doi,
    get_work_by_openalex_id,
)

router = APIRouter(
    prefix="/openalex",
    tags=["OpenAlex"]
)


@router.get(
    "/works/search",
    response_model=list[OpenAlexWorkPreview]
)
async def search_openalex_works(
    query: str = Query(..., min_length=2),
    per_page: int = Query(default=10, ge=1, le=25)
):
    try:
        return await search_works(query, per_page)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAlex request failed"
        )


@router.get(
    "/works/doi",
    response_model=OpenAlexWorkPreview
)
async def read_openalex_work_by_doi(
    doi: str = Query(..., min_length=3)
):
    try:
        work = await get_work_by_doi(doi)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAlex request failed"
        )

    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found in OpenAlex"
        )

    return work

@router.post(
    "/works/import",
    response_model=PublicationRead,
    status_code=status.HTTP_201_CREATED
)
async def import_openalex_work(
    import_data: OpenAlexImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile_by_user_id(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    try:
        work = await get_work_by_openalex_id(import_data.openalex_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAlex request failed"
        )

    if work.doi:
        existing_publication = get_publication_by_doi(
            db,
            profile.id,
            work.doi
        )

        if existing_publication:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Publication with this DOI already exists"
            )

    publication_data = PublicationCreate(
        title=work.title or "Untitled publication",
        abstract=None,
        publication_type=work.publication_type,
        publication_year=work.publication_year,
        doi=work.doi,
        journal_name=work.journal_name,
        conference_name=None,
        publisher=None,
        citation_count=work.citation_count,
        openalex_id=work.openalex_id,
        orcid_work_id=None
    )

    return create_publication(
        db,
        profile.id,
        publication_data
    )