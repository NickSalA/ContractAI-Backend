from abc import abstractmethod
from contractai_backend.core.application.base import BaseRepository
from contractai_backend.modules.chatbot.domain.entities import ConversationTable

class IConversationRepository(BaseRepository[ConversationTable]):
    @abstractmethod
    async def update_messages(self, conversation_id: int, new_messages: list[dict]) -> ConversationTable | None:
        pass

    @abstractmethod
    async def get_by_user(self, user_id: int) -> list[ConversationTable]:
        pass