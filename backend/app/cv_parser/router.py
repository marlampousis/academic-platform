from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.users.models import User
from app.users.router import get_current_user

from app.documents.service import get_document_by_id
from app.cv_parser.schemas import ParsedCVPreview, StructuredCVPreview, CVImportResponse
from app.cv_parser.service import parse_cv_text, build_structured_preview, import_parsed_cv_data

from app.profiles.service import get_profile_by_user_id
from app.documents.service import update_document_status

router = APIRouter(
    prefix="/cv-parser",
    tags=["CV Parser"]
)


@router.post(
    "/documents/{document_id}/preview",
    response_model=ParsedCVPreview
)
def preview_cv_parsing(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = get_document_by_id(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this document"
        )

    if not document.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document text has not been extracted yet"
        )

    return parse_cv_text(document.extracted_text)

@router.post(
    "/documents/{document_id}/structured-preview",
    response_model=StructuredCVPreview
)
def preview_structured_cv(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = get_document_by_id(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this document"
        )

    if not document.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document text has not been extracted"
        )

    return build_structured_preview(document.extracted_text)

@router.post(
    "/documents/{document_id}/import",
    response_model=CVImportResponse
)
def import_cv_data(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = get_document_by_id(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this document"
        )

    if not document.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document text has not been extracted"
        )

    profile = get_profile_by_user_id(
        db,
        current_user.id
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found"
        )

    parsed_data = build_structured_preview(
        document.extracted_text
    )

    import_result = import_parsed_cv_data(
        db=db,
        profile=profile,
        parsed_data=parsed_data
    )

    update_document_status(
        db=db,
        document=document,
        status_value="IMPORTED"
    )

    return {
        **import_result,
        "document_status": "IMPORTED"
    }