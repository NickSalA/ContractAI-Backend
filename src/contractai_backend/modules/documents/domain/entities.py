"""This module defines the entities related to documents in the ContractAI backend."""
from dataclasses import dataclass, field
from datetime import date, datetime

from .value_objs import DocumentPeriod, DocumentState, DocumentType, Money


@dataclass
class DocumentChunk:
    """Entity that represents a chunk to be stored in the vector database."""
    id: int
    document_id: int
    filename: str
    client: str
    content: str
    upload_at: datetime = field(default_factory=datetime.now(datetime.timezone.utc))
    
@dataclass
class Document:
    """Entity that represents a document with its metadata."""
    id: int
    name: str
    client: str
    type: DocumentType
    period: DocumentPeriod
    value: Money
    licenses: int
    state: DocumentState

    def is_expired(self) -> bool:
        """Determines if the document is expired based on the end date."""
        return date.today() > self.period.end
    
    def can_be_renewed(self) -> bool:
        """Determines if the document can be renewed based on its state and expiration."""
        return self.state == DocumentState.ACTIVE and self.is_expired()
