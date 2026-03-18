"""Contracts for vector indexing and retrieval."""
from typing import Any
from abc import ABC, abstractmethod


class IVectorRepository(ABC):
    """Stores vectorized document chunks and retrieves similar content."""

    @abstractmethod
    async def add_vectors(self, index_name: str, filename: str, chunks: list[Any]) -> None:
        """Adds vectorized chunks for a document."""
        pass

    @abstractmethod
    async def delete_vectors(self, index_name: str, filename: str) -> None:
        """Deletes all vectors associated with a document."""
        pass
