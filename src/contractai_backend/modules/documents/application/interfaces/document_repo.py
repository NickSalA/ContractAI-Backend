"""Interface for the Document Repository."""

from abc import abstractmethod
from typing import List

from src.contractai_backend.core.interfaces.base import IBaseRepository
from src.contractai_backend.modules.documents.domain.entities import Document


class IDocumentRepository(IBaseRepository[Document]):
    """Interface for the Document Repository."""

    @abstractmethod
    async def get_by_client_name(self, client_name: str) -> List[Document]:
        """Lists all documents for a given client."""
        pass

    @abstractmethod
    async def get_active_documents(self) -> List[Document]:
        """Lists all active documents."""
        pass
