"""Repository interface for invoking the Large Language Model (LLM) provider."""

from abc import ABC, abstractmethod

class ILLMProvider(ABC):
    @abstractmethod
    async def invoke(self, message: str, thread_id: int) -> tuple[str, int]:
        """Invokes the LLM provider with the given message and mandatory thread ID."""
        pass