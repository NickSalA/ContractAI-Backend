from abc import ABC, abstractmethod
from contractai_backend.modules.users.domain.entities import User

class IUserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        pass