"""Organization repository contracts."""

from abc import abstractmethod
from collections.abc import Sequence

from contractai_backend.core.application.base import BaseRepository
from contractai_backend.modules.organizations.domain.entities import OrganizationTable


class OrganizationRepository(BaseRepository[OrganizationTable]):
    """Base repository for organization persistence."""

    @abstractmethod
    async def get_by_name(self, name: str) -> OrganizationTable | None:
        """Retrieve an organization by its name."""
        pass

    @abstractmethod
    async def get_active(self) -> Sequence[OrganizationTable]:
        """Retrieve active organizations."""
        pass
