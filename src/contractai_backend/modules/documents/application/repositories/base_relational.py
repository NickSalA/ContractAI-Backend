"""Interface for the Document Repository."""

from abc import abstractmethod
from typing import List

from contractai_backend.core.application.base import BaseRepository
from contractai_backend.modules.documents.domain.entities import DocumentTable


class DocumentRepository(BaseRepository[DocumentTable]):
    """Interface for the Document Repository."""

    @abstractmethod
    async def get_by_client_name(self, client_name: str) -> List[DocumentTable]:
        """Lists all documents for a given client."""
        pass

    @abstractmethod
    async def get_active_documents(self) -> List[DocumentTable]:
        """Lists all active documents."""
        pass
