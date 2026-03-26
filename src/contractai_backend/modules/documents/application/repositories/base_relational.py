"""Interface for the Document Repository."""

from abc import abstractmethod
from collections.abc import Sequence

from .....core.application.base import BaseRepository
from ...domain.entities import DocumentServiceTable, DocumentTable, ServiceTable


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

    @abstractmethod
    async def get_document_services(self, document_id: int) -> Sequence[DocumentServiceTable]:
        """Lists the services associated to a document."""
        pass

    @abstractmethod
    async def get_document_services_by_document_ids(self, document_ids: Sequence[int]) -> dict[int, Sequence[DocumentServiceTable]]:
        """Lists services grouped by document id for many documents."""
        pass

    @abstractmethod
    async def replace_document_services(self, document_id: int, service_items: Sequence[DocumentServiceTable]) -> Sequence[DocumentServiceTable]:
        """Replaces the set of services associated to a document."""
        pass

    @abstractmethod
    async def get_services_by_ids(self, organization_id: int, service_ids: Sequence[int]) -> Sequence[ServiceTable]:
        """Retrieves the services that belong to an organization by id."""
        pass

    @abstractmethod
    async def get_services(self, organization_id: int) -> Sequence[ServiceTable]:
        """Retrieves the service catalog for an organization."""
        pass
