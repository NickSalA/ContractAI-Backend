"""Base repository interface defining common CRUD operations for entities."""
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")

class BaseRepository(Generic[T], ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        """Retrieves an entity by its ID. Returns None if not found."""
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        """Returns a list of all entities."""
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Saves an entity and returns the saved instance (with ID if applicable)."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> Optional[T]:
        """Update an entity by its ID. Returns the updated entity or None if not found."""
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Deletes an entity by its ID. Returns True if deletion was successful."""
        pass
