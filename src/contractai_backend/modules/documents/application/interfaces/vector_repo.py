"""Contracts for vector indexing and retrieval."""

from abc import ABC, abstractmethod


class IVectorRepository(ABC):
    """Stores vectorized document chunks and retrieves similar content."""

    @abstractmethod
    async def upsert_document_chunks(
        self,
        document_id: int,
        chunks: list[str],
        embeddings: list[list[float]],
        metadata: dict[str, str],
    ) -> None:
        """Upsert all chunks for a document."""
        raise NotImplementedError

    @abstractmethod
    async def delete_document_chunks(self, document_id: int) -> None:
        """Delete indexed chunks for a document."""
        raise NotImplementedError

    @abstractmethod
    async def search_document_ids(
        self,
        query_embedding: list[float],
        *,
        limit: int = 20,
        filters: dict[str, str] | None = None,
    ) -> list[int]:
        """Return ordered document ids that best match an embedding query."""
        raise NotImplementedError
