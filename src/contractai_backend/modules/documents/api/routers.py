"""Module containing API routers for document-related endpoints."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile, status
from pydantic import ValidationError

from ..application.repositories import DocumentRepository
from ..application.services import DocumentService
from .dependencies import get_document_repository, get_document_service
from .schemas import CreateDocumentRequest, DocumentFileUrlResponse, DocumentResponse, UpdateDocumentRequest

router = APIRouter()

DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
DocumentRepositoryDep = Annotated[DocumentRepository, Depends(get_document_repository)]


# TODO: Orquestar de mejor forma el Schema de document.
@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(file: UploadFile, service: DocumentServiceDep, document: str = Form(...)) -> DocumentResponse:
    """Endpoint to create a new document."""
    try:
        doc_data = json.loads(document)
        doc_obj = CreateDocumentRequest(**doc_data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    if file.filename is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must have a valid filename.")

    file_content = await file.read()

    saved_document = await service.create_document(
        file=file_content,
        filename=file.filename,
        data=doc_obj,
        content_type=file.content_type or "application/pdf",
    )

    return DocumentResponse.model_validate(saved_document)


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    repository: DocumentRepositoryDep,
) -> list[DocumentResponse]:
    """Endpoint to list documents with optional filters."""
    docs = await repository.get_all()
    return [DocumentResponse.model_validate(doc) for doc in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, repository: DocumentRepositoryDep) -> DocumentResponse:
    """Endpoint to retrieve a document by its ID."""
    doc = await repository.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.get("/{document_id}/file-url", response_model=DocumentFileUrlResponse)
async def get_document_file_url(document_id: int, service: DocumentServiceDep) -> DocumentFileUrlResponse:
    """Endpoint to generate a signed URL for a stored document file."""
    url = await service.get_document_signed_url(id=document_id)
    return DocumentFileUrlResponse(url=url)


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    service: DocumentServiceDep,
    document: str = Form(...),
    file: UploadFile | None = None,
) -> DocumentResponse:
    """Endpoint to update an existing document."""
    try:
        doc_data = json.loads(document)
        doc_obj = UpdateDocumentRequest(**doc_data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    file_content = await file.read() if file else None

    updated_doc = await service.update_document(
        id=document_id,
        data=doc_obj,
        file=file_content,
        filename=file.filename if file else None,
        content_type=file.content_type or "application/pdf" if file else "application/pdf",
    )
    return DocumentResponse.model_validate(updated_doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_document(document_id: int, service: DocumentServiceDep) -> None:
    """Endpoint to delete a document by its ID."""
    await service.delete_document(document_id)
