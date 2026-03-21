from abc import ABC, abstractmethod
from contractai_backend.modules.users.domain.entities import User

class ITokenService(ABC):
    @abstractmethod
    def create_access_token(self, user: User) -> str:
        pass