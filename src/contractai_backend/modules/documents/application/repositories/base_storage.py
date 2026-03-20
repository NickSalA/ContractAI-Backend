"""Interface for document binary storage providers."""

from abc import ABC, abstractmethod


class DocumentStorageRepository(ABC):
    """Defines operations to store, remove and share document files."""

    @abstractmethod
    async def upload_file(self, *, path: str, file: bytes, content_type: str) -> None:
        """Uploads a document file to storage."""

    @abstractmethod
    async def delete_file(self, *, path: str) -> None:
        """Deletes a document file from storage if it exists."""

    @abstractmethod
    async def create_signed_url(self, *, path: str, expires_in: int = 3600) -> str:
        """Creates a signed URL for temporary file access."""
