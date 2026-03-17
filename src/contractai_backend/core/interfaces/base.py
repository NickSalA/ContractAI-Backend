"""Base repository interface for the ContractAI backend."""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")
ID = TypeVar("ID")

class IBaseRepository(ABC, Generic[T]):
    """Generic interface for a repository."""

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Saves an entity to the repository."""
        pass

    @abstractmethod
    async def get_by_id(self, id: ID) -> Optional[T]:
        """Retrieves an entity by its ID."""
        pass

    @abstractmethod
    async def list_all(self) -> List[T]:
        """Lists all entities in the repository."""
        pass

    @abstractmethod
    async def delete(self, id: ID) -> None:
        """Deletes an entity by its ID."""
        pass

    @abstractmethod
    async def update(self, id: ID, entity: T) -> Optional[T]:
        """Updates an entity by its ID."""
        pass
