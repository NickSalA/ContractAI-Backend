"""Module containing API routers for document-related endpoints."""

from fastapi import APIRouter, Depends, UploadFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.modules.documents.infrastructure.model import DocumentTable
from contractai_backend.shared.database.database import get_session

from .schemas import CreateDocumentRequest, DocumentResponse, UpdateDocumentRequest

router = APIRouter()

@router.post("/", response_model=DocumentResponse)
async def create_document(file: UploadFile, document: CreateDocumentRequest) -> DocumentResponse:
    """Endpoint to create a new document."""
    # Implementation goes here
    raise NotImplementedError

@router.get("/", response_model=list[DocumentResponse])
async def list_documents(session: AsyncSession = Depends(get_session)) -> list[DocumentResponse]:
    """Endpoint to list documents with optional filters."""
    query = select(DocumentTable)
    result = await session.exec(query)
    documents = result.all()
    return [
        DocumentResponse(
            id=document.id,
            name=document.name,
            client=document.client,
            type=document.type,
            start_date=document.start,
            end_date=document.end,
            value=document.value,
            currency=document.currency,
            licenses=document.licenses,
            state=document.state,
        )
        for document in documents
    ]

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int) -> DocumentResponse:
    """Endpoint to retrieve a document by its ID."""
    # Implementation goes here
    raise NotImplementedError

@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: int, document: UpdateDocumentRequest) -> DocumentResponse:
    """Endpoint to update an existing document."""
    # Implementation goes here
    raise NotImplementedError

@router.delete("/{document_id}")
async def delete_document(document_id: int) -> None:
    """Endpoint to delete a document by its ID."""
    # Implementation goes here
    pass
