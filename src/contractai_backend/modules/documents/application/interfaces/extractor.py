"""Module containing the IExtractor interface for document data extraction."""

from abc import ABC, abstractmethod
from typing import Any, List


class IExtractor(ABC):
    """Interface for document extractors."""
    @abstractmethod
    async def extract(self, file_bytes: bytes) -> List[Any]:
        """Extracts structured data from a document file."""
        pass
