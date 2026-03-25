"""Module containing API routers for document-related endpoints."""

import json
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Response, UploadFile, status
from pydantic import ValidationError

from ....shared.api.dependencies.security import CurrentUserDep
from ..application.repositories import DocumentRepository
from ..application.services import DocumentService
from ..domain.entities import DocumentTable
from ..domain.exceptions import DocumentNotFoundError, DocumentValidationError, InvalidDocumentFileError
from .dependencies import get_document_repository, get_document_service
from .schemas import CreateDocumentRequest, DocumentFileUrlResponse, DocumentResponse, FileRequest, UpdateDocumentRequest

router = APIRouter()

DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
DocumentRepositoryDep = Annotated[DocumentRepository, Depends(get_document_repository)]


@router.post(path="/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    file: UploadFile,
    service: DocumentServiceDep,
    current_user: CurrentUserDep,
    document: str = Form(...),
) -> DocumentResponse:
    """Endpoint to create a new document."""
    try:
        doc_data = json.loads(document)
        doc_obj = CreateDocumentRequest(**doc_data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise DocumentValidationError(f"Datos del documento invalidos: {e}") from e

    if file.filename is None or file.content_type is None:
        raise InvalidDocumentFileError()

    file_content: bytes = await file.read()
    file_data = FileRequest(content=file_content, filename=file.filename, content_type=file.content_type)

    saved_document = await service.create_document(
        data=doc_obj,
        file_data=file_data,
        organization_id=current_user.organization_id,
    )
    return DocumentResponse.model_validate(obj=saved_document)


@router.get(path="/", response_model=Sequence[DocumentResponse])
async def list_documents(repository: DocumentRepositoryDep, current_user: CurrentUserDep) -> Sequence[DocumentResponse]:
    """Endpoint to list documents with optional filters."""
    docs: Sequence[DocumentTable] = await repository.get_all(filters={"organization_id": current_user.organization_id})
    return [DocumentResponse.model_validate(obj=doc) for doc in docs]


@router.get(path="/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, repository: DocumentRepositoryDep, current_user: CurrentUserDep) -> DocumentResponse:
    """Endpoint to retrieve a document by its ID."""
    doc = await repository.get_by_id(id=document_id)
    if not doc or doc.organization_id != current_user.organization_id:
        raise DocumentNotFoundError(document_id=document_id)
    return DocumentResponse.model_validate(obj=doc)


@router.get(path="/{document_id}/file-url", response_model=DocumentFileUrlResponse)
async def get_document_file_url(document_id: int, service: DocumentServiceDep, current_user: CurrentUserDep) -> DocumentFileUrlResponse:
    """Endpoint to generate a signed URL for a stored document file."""
    url = await service.get_document_signed_url(id=document_id, organization_id=current_user.organization_id)
    return DocumentFileUrlResponse(url=url)


@router.patch(path="/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    service: DocumentServiceDep,
    current_user: CurrentUserDep,
    document: str = Form(...),
    file: UploadFile | None = None,
) -> DocumentResponse:
    """Endpoint to update an existing document."""
    try:
        doc_data = json.loads(document)
        doc_obj = UpdateDocumentRequest(**doc_data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise DocumentValidationError(f"Datos del documento invalidos: {e}") from e

    file_data = None
    if file:
        file_content: bytes = await file.read()
        if file.filename is None or file.content_type is None:
            raise InvalidDocumentFileError()
        file_data = FileRequest(content=file_content, filename=file.filename, content_type=file.content_type)

    updated_doc = await service.update_document(
        id=document_id,
        data=doc_obj,
        organization_id=current_user.organization_id,
        file_data=file_data,
    )
    return DocumentResponse.model_validate(obj=updated_doc)


@router.delete(path="/{document_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_document(document_id: int, service: DocumentServiceDep, current_user: CurrentUserDep) -> None:
    """Endpoint to delete a document by its ID."""
    await service.delete_document(id=document_id, organization_id=current_user.organization_id)
