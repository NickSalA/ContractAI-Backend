"""Module containing API routers for document-related endpoints."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status

from ..application.services import DocumentService
from .dependencies import get_document_service
from .schemas import CreateDocumentRequest, DocumentResponse, UpdateDocumentRequest

router = APIRouter()

DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]

# TODO: Orquestar de mejor forma el Schema de document.
@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(file: UploadFile, service: DocumentServiceDep, document: str = Form(...)) -> DocumentResponse:
    """Endpoint to create a new document."""
    try:
        doc_data = json.loads(document)
        doc_obj = CreateDocumentRequest(**doc_data)
        file_content = await file.read()

        saved_document = await service.create_document(
            file=file_content,
            filename=file.filename,
            data=doc_obj
        )
        return saved_document
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    service: DocumentServiceDep,
) -> list[DocumentResponse]:
    """Endpoint to list documents with optional filters."""
    return await service.get_documents()

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, service: DocumentServiceDep) -> DocumentResponse:
    """Endpoint to retrieve a document by its ID."""
    document = await service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document

#TODO: Implementar endpoint de actualización (PATCH)
@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: int, document: UpdateDocumentRequest, service: DocumentServiceDep) -> DocumentResponse:
    """Endpoint to update an existing document."""
    # Implementation goes here
    pass

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int, service: DocumentServiceDep) -> None:
    """Endpoint to delete a document by its ID."""
    document = await service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    try:
        await service.delete_document(id=document_id, filename=document.name)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
