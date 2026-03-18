"""Schemas for document-related API requests and responses."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from contractai_backend.modules.documents.domain.entities import DocumentState, DocumentType


class DocumentBase(BaseModel):
    """Base schema for document-related requests."""

    name: str = Field(..., description="Name of the document")
    client: str = Field(..., description="Client associated with the document")
    type: DocumentType = Field(..., description="Type of the document (e.g., LICENSES, SERVICES)")
    start_date: date = Field(..., description="Start date of the document period")
    end_date: date = Field(..., description="End date of the document period")
    value: float = Field(..., description="Monetary value of the document")
    currency: str = Field(..., description="Currency code for the document value (e.g., PEN)")
    licenses: int = Field(..., description="Number of licenses covered by the document")

class CreateDocumentRequest(DocumentBase):
    """Request schema for creating a new document."""
    pass

class UpdateDocumentRequest(DocumentBase):
    """Request schema for updating an existing document."""
    name: str | None
    client: str | None
    type: DocumentType | None
    start_date: date | None
    end_date: date | None
    value: float | None
    currency: str | None
    state: DocumentState | None

class DocumentResponse(DocumentBase):
    """Response schema for document data."""
    id: int = Field(..., description="Unique identifier of the document")
    state: DocumentState = Field(..., description="Current state of the document (e.g., ACTIVE, EXPIRED)")

    model_config = ConfigDict(from_attributes=True)
