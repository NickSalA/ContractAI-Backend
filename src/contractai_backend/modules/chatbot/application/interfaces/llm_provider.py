from abc import ABC, abstractmethod

class ILLMProvider(ABC):
    @abstractmethod
    def invoke(self, message: str, thread_id: int | None) -> tuple[str, int]:
        pass