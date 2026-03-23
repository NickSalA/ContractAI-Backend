from sqlmodel.ext.asyncio.session import AsyncSession
from contractai_backend.core.infrastructure.base import PostgresBaseRepository
from contractai_backend.modules.chatbot.application.repositories.base_relational import IHistoryRepository
from contractai_backend.modules.chatbot.domain.entities import ChatMessageTable

class PostgresHistoryRepository(PostgresBaseRepository[ChatMessageTable], IHistoryRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ChatMessageTable)