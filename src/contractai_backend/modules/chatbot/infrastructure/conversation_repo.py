from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from contractai_backend.core.infrastructure.base import PostgresBaseRepository
from contractai_backend.modules.chatbot.domain.entities import ConversationTable
from contractai_backend.modules.chatbot.application.repositories.base_conversation import IConversationRepository


class ConversationRepository(PostgresBaseRepository[ConversationTable], IConversationRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(model=ConversationTable, session=session)

    async def update_messages(self, conversation_id: int, new_messages: list[dict]) -> ConversationTable | None:
        db_obj = await self.get(id=conversation_id)
        if not db_obj:
            return None

        current_content = list(db_obj.content) if db_obj.content else []
        current_content.extend(new_messages)

        db_obj.content = current_content
        db_obj.updated_at = datetime.now(timezone.utc)

        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)

        return db_obj

    async def get_by_user(self, user_id: int) -> list[ConversationTable]:
        query = select(self.model).where(self.model.user_id == user_id).order_by(self.model.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())