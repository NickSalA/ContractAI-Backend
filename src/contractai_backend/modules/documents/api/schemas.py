"""Schemas for document-related API requests and responses."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from ....modules.documents.domain import DocumentState, DocumentType


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


class UpdateDocumentRequest(BaseModel):
    """Request schema for updating an existing document."""

    name: str | None = None
    client: str | None = None
    type: DocumentType | None = None
    start_date: date | None = None
    end_date: date | None = None
    value: float | None = None
    currency: str | None = None
    state: DocumentState | None = None


class DocumentResponse(DocumentBase):
    """Response schema for document data."""

    id: int = Field(..., description="Unique identifier of the document")
    state: DocumentState = Field(..., description="Current state of the document (e.g., ACTIVE, EXPIRED)")
    file_path: str | None = Field(default=None, description="Storage path of the associated file")
    file_name: str | None = Field(default=None, description="Original name of the associated file")

    model_config = ConfigDict(from_attributes=True)


class DocumentFileUrlResponse(BaseModel):
    """Response schema with a temporary URL to access a document file."""

    url: str = Field(..., description="Signed URL for temporary access")

class FileRequest(BaseModel):
    """Request schema for file uploads."""

    content: bytes = Field(..., description="Binary content of the file", repr=False)
    filename: str = Field(..., description="Original name of the file")
    content_type: str = Field(..., description="MIME type of the file")
