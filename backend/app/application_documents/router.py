from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.users.models import User
from app.users.router import get_current_user

from app.applications.service import (
    get_application_by_id,
)

from app.documents.service import (
    get_document_by_id,
)

from app.position_required_documents.service import (
    get_required_document_by_type,
)

from app.application_documents.schemas import (
    ApplicationDocumentCreate,
    ApplicationDocumentRead,
)

from app.application_documents.service import (
    create_application_document,
    delete_application_document,
    get_application_document_by_document,
    get_application_document_by_id,
    get_application_documents,
)


router = APIRouter(
    prefix="/applications",
    tags=["Application Documents"],
)


@router.post(
    "/{application_id}/documents",
    response_model=ApplicationDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def attach_document_to_application(
    application_id: int,
    application_document_data: ApplicationDocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = get_application_by_id(
        db,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to modify this application",
        )

    if application.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documents can only be attached to draft applications",
        )

    document = get_document_by_id(
        db,
        application_document_data.document_id,
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to use this document",
        )

    existing_application_document = (
        get_application_document_by_document(
            db,
            application_id,
            document.id,
        )
    )

    if existing_application_document:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already attached to this application",
        )

    configured_document_type = get_required_document_by_type(
        db=db,
        position_id=application.position_id,
        document_type_id=document.document_type_id,
    )

    if not configured_document_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "This document type is not configured "
                "for the selected position"
            ),
        )

    return create_application_document(
        db=db,
        application_id=application.id,
        document_id=document.id,
        source="PROFILE",
    )


@router.get(
    "/{application_id}/documents",
    response_model=list[ApplicationDocumentRead],
)
def read_application_documents(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = get_application_by_id(
        db,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this application",
        )

    return get_application_documents(
        db,
        application_id,
    )


@router.delete(
    "/{application_id}/documents/{application_document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_document_from_application(
    application_id: int,
    application_document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = get_application_by_id(
        db,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to modify this application",
        )

    if application.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documents can only be removed from draft applications",
        )

    application_document = (
        get_application_document_by_id(
            db,
            application_document_id,
        )
    )

    if (
        not application_document
        or application_document.application_id
        != application_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application document not found",
        )

    delete_application_document(
        db,
        application_document,
    )