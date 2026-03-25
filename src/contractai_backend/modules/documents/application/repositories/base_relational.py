"""Interface for the Document Repository."""

from abc import abstractmethod
from collections.abc import Sequence

from .....core.application.base import BaseRepository
from ...domain.entities import DocumentTable


class DocumentRepository(BaseRepository[DocumentTable]):
    """Interface for the Document Repository."""

    @abstractmethod
    async def get_by_client_name(self, client_name: str) -> Sequence[DocumentTable]:
        """Lists all documents for a given client."""
        pass

    @abstractmethod
    async def get_active_documents(self) -> Sequence[DocumentTable]:
        """Lists all active documents."""
        pass
