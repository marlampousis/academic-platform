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

from app.academic_positions.service import (
    get_position_by_id,
)
from app.document_types.service import (
    get_document_type_by_id,
)

from app.position_required_documents.schemas import (
    PositionRequiredDocumentCreate,
    PositionRequiredDocumentRead,
    PositionRequiredDocumentUpdate,
)
from app.position_required_documents.service import (
    create_required_document,
    delete_required_document,
    get_required_document_by_id,
    get_required_document_by_type,
    get_required_documents_by_position,
    update_required_document,
)


router = APIRouter(
    prefix="/positions",
    tags=["Position Required Documents"],
)


@router.post(
    "/{position_id}/required-documents",
    response_model=PositionRequiredDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def add_required_document(
    position_id: int,
    required_document_data: PositionRequiredDocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    position = get_position_by_id(
        db,
        position_id,
    )

    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )

    if position.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to modify this position",
        )

    document_type = get_document_type_by_id(
        db,
        required_document_data.document_type_id,
    )

    if not document_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document type not found",
        )

    if not document_type.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document type is inactive",
        )

    existing_required_document = (
        get_required_document_by_type(
            db,
            position_id,
            required_document_data.document_type_id,
        )
    )

    if existing_required_document:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Document type is already configured "
                "for this position"
            ),
        )

    return create_required_document(
        db=db,
        position_id=position_id,
        required_document_data=required_document_data,
    )


@router.get(
    "/{position_id}/required-documents",
    response_model=list[PositionRequiredDocumentRead],
)
def read_required_documents(
    position_id: int,
    db: Session = Depends(get_db),
):
    position = get_position_by_id(
        db,
        position_id,
    )

    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )

    return get_required_documents_by_position(
        db,
        position_id,
    )


@router.put(
    "/{position_id}/required-documents/{required_document_id}",
    response_model=PositionRequiredDocumentRead,
)
def edit_required_document(
    position_id: int,
    required_document_id: int,
    required_document_data: PositionRequiredDocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    position = get_position_by_id(
        db,
        position_id,
    )

    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )

    if position.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to modify this position",
        )

    required_document = get_required_document_by_id(
        db,
        required_document_id,
    )

    if (
        not required_document
        or required_document.position_id != position_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Required document not found",
        )

    return update_required_document(
        db,
        required_document,
        required_document_data,
    )


@router.delete(
    "/{position_id}/required-documents/{required_document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_required_document(
    position_id: int,
    required_document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    position = get_position_by_id(
        db,
        position_id,
    )

    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )

    if position.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to modify this position",
        )

    required_document = get_required_document_by_id(
        db,
        required_document_id,
    )

    if (
        not required_document
        or required_document.position_id != position_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Required document not found",
        )

    delete_required_document(
        db,
        required_document,
    )