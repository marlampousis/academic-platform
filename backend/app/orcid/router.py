from fastapi import APIRouter, HTTPException, status, Depends

from app.orcid.client import get_orcid_profile, get_orcid_works, get_orcid_education
from app.orcid.schemas import (
    OrcidProfilePreview,
    OrcidWorkPreview,
    OrcidImportWorksResponse,
    OrcidEducationPreview,
    OrcidImportEducationResponse,
    OrcidImportProfileResponse,
    OrcidSyncResponse,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.users.models import User
from app.users.router import get_current_user
from app.profiles.service import get_profile_by_user_id

from app.publications.schemas import PublicationCreate
from app.publications.service import (
    create_publication,
    get_publication_by_doi,
)

from app.orcid.schemas import OrcidImportWorksResponse

from app.degrees.schemas import DegreeCreate
from app.degrees.service import create_degree, get_duplicate_degree

from app.profiles.service import update_profile
from app.profiles.schemas import AcademicProfileUpdate

router = APIRouter(
    prefix="/orcid",
    tags=["ORCID"]
)


@router.get(
    "/profile/{orcid_id}",
    response_model=OrcidProfilePreview
)
async def read_orcid_profile(orcid_id: str):
    try:
        return await get_orcid_profile(orcid_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ORCID request failed"
        )

@router.post(
    "/profile/{orcid_id}/import",
    response_model=OrcidImportProfileResponse
)
async def import_orcid_profile(
    orcid_id: str,
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
        orcid_profile = await get_orcid_profile(orcid_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ORCID request failed"
        )

    profile_data = AcademicProfileUpdate(
        orcid_id=orcid_profile.orcid_id,
        biography=orcid_profile.biography or profile.biography
    )

    update_profile(db, profile, profile_data)

    return {
        "message": "ORCID profile imported successfully",
        "orcid_id": orcid_id
    }

@router.get(
    "/works/{orcid_id}",
    response_model=list[OrcidWorkPreview]
)
async def read_orcid_works(orcid_id: str):
    try:
        return await get_orcid_works(orcid_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ORCID request failed"
        )
        
@router.post(
    "/works/{orcid_id}/import",
    response_model=OrcidImportWorksResponse
)
async def import_orcid_works(
    orcid_id: str,
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
        works = await get_orcid_works(orcid_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ORCID request failed"
        )

    imported_count = 0
    skipped_count = 0

    for work in works:
        if not work.title:
            skipped_count += 1
            continue

        if work.doi:
            existing_publication = get_publication_by_doi(
                db,
                profile.id,
                work.doi
            )

            if existing_publication:
                skipped_count += 1
                continue

        publication_data = PublicationCreate(
            title=work.title,
            abstract=None,
            publication_type=work.work_type,
            publication_year=work.publication_year,
            doi=work.doi,
            journal_name=work.journal_title,
            conference_name=None,
            publisher=None,
            citation_count=0,
            openalex_id=None,
            orcid_work_id=work.orcid_work_id
        )

        create_publication(
            db,
            profile.id,
            publication_data
        )

        imported_count += 1

    return {
        "imported_count": imported_count,
        "skipped_count": skipped_count
    }        
        
@router.get(
    "/education/{orcid_id}",
    response_model=list[OrcidEducationPreview]
)
async def read_orcid_education(orcid_id: str):
    try:
        return await get_orcid_education(orcid_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ORCID request failed"
        )


@router.post(
    "/education/{orcid_id}/import",
    response_model=OrcidImportEducationResponse
)
async def import_orcid_education(
    orcid_id: str,
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
        education_entries = await get_orcid_education(orcid_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ORCID request failed"
        )

    imported_count = 0
    skipped_count = 0

    for education in education_entries:
        if not education.organization_name:
            skipped_count += 1
            continue

        degree_type = "Education"
        title = education.role_title or "Academic Education"
        institution_name = education.organization_name

        existing_degree = get_duplicate_degree(
            db,
            profile.id,
            degree_type,
            title,
            institution_name,
            education.end_year
        )

        if existing_degree:
            skipped_count += 1
            continue

        degree_data = DegreeCreate(
            degree_type=degree_type,
            title=title,
            field_of_study=education.department_name,
            institution_name=institution_name,
            country=None,
            start_year=education.start_year,
            end_year=education.end_year
        )

        create_degree(db, profile.id, degree_data)

        imported_count += 1

    return {
        "imported_count": imported_count,
        "skipped_count": skipped_count
    }        
    
@router.post(
    "/sync/{orcid_id}",
    response_model=OrcidSyncResponse
)
async def sync_orcid_profile(
    orcid_id: str,
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
        orcid_profile = await get_orcid_profile(orcid_id)
        works = await get_orcid_works(orcid_id)
        education_entries = await get_orcid_education(orcid_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ORCID request failed"
        )

    profile_data = AcademicProfileUpdate(
        orcid_id=orcid_profile.orcid_id,
        biography=orcid_profile.biography or profile.biography
    )

    update_profile(db, profile, profile_data)

    works_imported = 0
    works_skipped = 0

    for work in works:
        if not work.title:
            works_skipped += 1
            continue

        if work.doi:
            existing_publication = get_publication_by_doi(
                db,
                profile.id,
                work.doi
            )

            if existing_publication:
                works_skipped += 1
                continue

        publication_data = PublicationCreate(
            title=work.title,
            abstract=None,
            publication_type=work.work_type,
            publication_year=work.publication_year,
            doi=work.doi,
            journal_name=work.journal_title,
            conference_name=None,
            publisher=None,
            citation_count=0,
            openalex_id=None,
            orcid_work_id=work.orcid_work_id
        )

        create_publication(db, profile.id, publication_data)
        works_imported += 1

    education_imported = 0
    education_skipped = 0

    for education in education_entries:
        if not education.organization_name:
            education_skipped += 1
            continue

        degree_type = "Education"
        title = education.role_title or "Academic Education"
        institution_name = education.organization_name

        existing_degree = get_duplicate_degree(
            db,
            profile.id,
            degree_type,
            title,
            institution_name,
            education.end_year
        )

        if existing_degree:
            education_skipped += 1
            continue

        degree_data = DegreeCreate(
            degree_type=degree_type,
            title=title,
            field_of_study=education.department_name,
            institution_name=institution_name,
            country=None,
            start_year=education.start_year,
            end_year=education.end_year
        )

        create_degree(db, profile.id, degree_data)
        education_imported += 1

    return {
        "message": "ORCID synchronization completed successfully",
        "orcid_id": orcid_id,
        "works_imported": works_imported,
        "works_skipped": works_skipped,
        "education_imported": education_imported,
        "education_skipped": education_skipped
    }    