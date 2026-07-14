from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.document_types.schemas import (
    DocumentTypeCreate,
    DocumentTypeRead,
    DocumentTypeUpdate,
)

from app.document_types.service import (
    create_document_type,
    delete_document_type,
    get_active_document_types,
    get_all_document_types,
    get_document_type_by_code,
    get_document_type_by_id,
    update_document_type,
)


router = APIRouter(
    prefix="/document-types",
    tags=["Document Types"],
)


@router.get(
    "/",
    response_model=list[DocumentTypeRead],
)
def read_document_types(
    db: Session = Depends(get_db),
):
    return get_all_document_types(db)


@router.get(
    "/active",
    response_model=list[DocumentTypeRead],
)
def read_active_document_types(
    db: Session = Depends(get_db),
):
    return get_active_document_types(db)


@router.get(
    "/code/{code}",
    response_model=DocumentTypeRead,
)
def read_document_type_by_code(
    code: str,
    db: Session = Depends(get_db),
):
    document_type = get_document_type_by_code(
        db,
        code,
    )

    if not document_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document type not found",
        )

    return document_type


@router.get(
    "/{document_type_id}",
    response_model=DocumentTypeRead,
)
def read_document_type(
    document_type_id: int,
    db: Session = Depends(get_db),
):
    document_type = get_document_type_by_id(
        db,
        document_type_id,
    )

    if not document_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document type not found",
        )

    return document_type


@router.post(
    "/",
    response_model=DocumentTypeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_new_document_type(
    document_type_data: DocumentTypeCreate,
    db: Session = Depends(get_db),
):
    existing_document_type = get_document_type_by_code(
        db,
        document_type_data.code,
    )

    if existing_document_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document type code already exists",
        )

    return create_document_type(
        db,
        document_type_data,
    )


@router.put(
    "/{document_type_id}",
    response_model=DocumentTypeRead,
)
def edit_document_type(
    document_type_id: int,
    document_type_data: DocumentTypeUpdate,
    db: Session = Depends(get_db),
):
    document_type = get_document_type_by_id(
        db,
        document_type_id,
    )

    if not document_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document type not found",
        )

    return update_document_type(
        db,
        document_type,
        document_type_data,
    )


@router.delete(
    "/{document_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_document_type(
    document_type_id: int,
    db: Session = Depends(get_db),
):
    document_type = get_document_type_by_id(
        db,
        document_type_id,
    )

    if not document_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document type not found",
        )

    delete_document_type(
        db,
        document_type,
    )