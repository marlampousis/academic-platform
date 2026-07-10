import os
import shutil
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.users.models import User
from app.users.router import get_current_user
from app.profiles.service import get_profile_by_user_id

from app.documents.schemas import DocumentRead, DocumentTextRead
from app.documents.service import (
    create_document,
    get_documents_by_user_id,
    get_document_by_id,
    update_document_extracted_text,
)
from app.documents.utils.text_extraction import extract_text_from_document

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


UPLOAD_DIR = "uploads"

ALLOWED_FILE_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx"
}


@router.post(
    "/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED
)
def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed"
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    extension = ALLOWED_FILE_TYPES[file.content_type]
    unique_file_name = f"{uuid4()}{extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    profile = get_profile_by_user_id(db, current_user.id)

    document = create_document(
        db=db,
        user_id=current_user.id,
        profile_id=profile.id if profile else None,
        file_name=file.filename,
        file_path=file_path,
        file_type=file.content_type,
        document_type="CV"
    )

    return document


@router.get("/me", response_model=list[DocumentRead])
def read_my_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_documents_by_user_id(db, current_user.id)

@router.post(
    "/{document_id}/extract-text",
    response_model=DocumentTextRead
)
def extract_document_text(
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

    try:
        extracted_text = extract_text_from_document(
            document.file_path,
            document.file_type
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Text extraction failed"
        )

    return update_document_extracted_text(
        db,
        document,
        extracted_text
    )