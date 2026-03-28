"""Relational repository contracts for the documents module."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date
from typing import Any

from ...domain import DocumentServiceTable, DocumentTable, ServiceTable


class DocumentQueryRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> DocumentTable | None:
        """Returns one document by id."""
        pass

    @abstractmethod
    async def get_all(self, filters: dict[str, Any] | None = None) -> Sequence[DocumentTable]:
        """Lists documents matching optional filters."""
        pass

    @abstractmethod
    async def get_document_services(self, document_id: int) -> Sequence[DocumentServiceTable]:
        """Lists service items for one document."""
        pass

    @abstractmethod
    async def get_document_services_by_document_ids(self, document_ids: Sequence[int]) -> dict[int, Sequence[DocumentServiceTable]]:
        """Lists service items grouped by document id."""
        pass

    @abstractmethod
    async def search_contracts(
        self,
        organization_id: int,
        client: str | None = None,
        contract_name: str | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        currency: str | None = None,
        state: str | None = None,
        document_type: str | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
        date_mode: str = "overlap",
        limit: int | None = None,
    ) -> Sequence[DocumentTable]:
        """Lists contracts matching structured filters."""
        pass

    @abstractmethod
    async def count_contracts(
        self,
        organization_id: int,
        client: str | None = None,
        contract_name: str | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        currency: str | None = None,
        state: str | None = None,
        document_type: str | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
        date_mode: str = "overlap",
    ) -> int:
        """Counts contracts matching structured filters."""
        pass


class DocumentCommandRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> DocumentTable | None:
        """Returns one document by id."""
        pass

    @abstractmethod
    async def save(self, entity: DocumentTable) -> DocumentTable:
        """Persists a new document."""
        pass

    @abstractmethod
    async def update(self, entity: DocumentTable) -> DocumentTable:
        """Persists changes to a document."""
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Deletes a document by id."""
        pass

    @abstractmethod
    async def replace_document_services(self, document_id: int, service_items: Sequence[DocumentServiceTable]) -> Sequence[DocumentServiceTable]:
        """Replaces all service items for a document."""
        pass


class ServiceCatalogRepository(ABC):
    @abstractmethod
    async def get_services_by_ids(self, organization_id: int, service_ids: Sequence[int]) -> Sequence[ServiceTable]:
        """Returns catalog services for the given ids."""
        pass

    @abstractmethod
    async def get_services(self, organization_id: int) -> Sequence[ServiceTable]:
        """Lists the catalog for one organization."""
        pass
