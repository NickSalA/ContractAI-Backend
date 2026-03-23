from abc import ABC

from contractai_backend.core.application.base import BaseRepository
from contractai_backend.modules.chatbot.domain.entities import ChatMessageTable

class IHistoryRepository(BaseRepository[ChatMessageTable], ABC):
    pass