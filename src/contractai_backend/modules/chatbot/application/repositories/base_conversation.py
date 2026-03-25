"""Repository for managing conversations in the database."""

from abc import abstractmethod
from collections.abc import Sequence

from .....core.application.base import BaseRepository
from ...domain.entities import ConversationTable, Message


class IConversationRepository(BaseRepository[ConversationTable]):
    @abstractmethod
    async def update_messages(self, conversation_id: int, new_message: list[Message]) -> ConversationTable | None:
        """Actualiza el contenido de una conversación existente agregando nuevos mensajes."""
        pass

    @abstractmethod
    async def get_by_user(self, user_id: int) -> Sequence[ConversationTable]:
        """Obtiene una lista de conversaciones asociadas a un usuario específico."""
        pass
