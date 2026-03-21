"""Interface for the Document Repository."""

from abc import abstractmethod

from contractai_backend.core.application.base import BaseRepository
from contractai_backend.modules.documents.domain.entities import DocumentTable


class DocumentRepository(BaseRepository[DocumentTable]):
    """Interface for the Document Repository."""

    @abstractmethod
    async def get_by_client_name(self, client_name: str) -> list[DocumentTable]:
        """Lists all documents for a given client."""
        pass

    @abstractmethod
    async def get_active_documents(self) -> list[DocumentTable]:
        """Lists all active documents."""
        pass
