from abc import ABC, abstractmethod

class IVectorRepository(ABC):
    @abstractmethod
    def search_documents(self, query: str, limit: int = 5) -> str:
        pass