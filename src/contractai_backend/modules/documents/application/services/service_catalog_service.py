"""Service for operations related to the service catalog."""

from collections.abc import Sequence

from ...domain import ServiceTable
from ..repositories import ServiceCatalogRepository


class ServiceCatalogService:
    def __init__(self, sql_repo: ServiceCatalogRepository):
        """Stores the repo used to query catalog services."""
        self.sql_repo = sql_repo

    async def list_services(self, organization_id: int) -> Sequence[ServiceTable]:
        """Lists services available for the organization."""
        return await self.sql_repo.get_services(organization_id=organization_id)
