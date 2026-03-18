"""Domain entities for document management."""

from dataclasses import dataclass
from datetime import date

from contractai_backend.shared.config import settings

from .value_objs import DocumentPeriod, DocumentState, DocumentType, Money


@dataclass
class Document:
    """Document aggregate root with metadata and lifecycle behavior."""

    id: int
    name: str
    client: str
    type: DocumentType
    period: DocumentPeriod
    value: Money
    licenses: int
    state: DocumentState

    def is_expired(self) -> bool:
        """Return whether the document is already expired."""
        return date.today() > self.period.end

    def can_be_renewed(self) -> bool:
        """Return whether renewal is currently valid."""
        return self.state == DocumentState.ACTIVE and self.is_expired()

    def is_pending(self) -> bool:
        """Return whether the document should be flagged as pending expiry."""
        return self.state == DocumentState.ACTIVE and not self.is_expired() and (self.period.end - date.today()).days <= settings.PENDING_DAYS
