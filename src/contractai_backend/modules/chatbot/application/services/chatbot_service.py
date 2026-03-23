import random
from contractai_backend.modules.chatbot.application.repositories.base_llm import ILLMProvider
from contractai_backend.modules.chatbot.application.repositories.base_relational import IHistoryRepository
from contractai_backend.modules.chatbot.domain.entities import ChatMessageTable


class ChatbotService:
    def __init__(self, llm_provider: ILLMProvider, db_repo: IHistoryRepository):
        self.llm_provider = llm_provider
        self.db_repo = db_repo

    async def process_user_message(self, message: str, thread_id: int | None = None) -> tuple[str, int]:
        current_thread_id = thread_id if thread_id is not None else random.randint(10000, 99999)

        user_msg = ChatMessageTable(role="user", content=message, thread_id=current_thread_id)
        await self.db_repo.save(entity=user_msg)

        response_text, actual_thread_id = await self.llm_provider.invoke(
            message=message,
            thread_id=current_thread_id
        )

        bot_msg = ChatMessageTable(role="assistant", content=response_text, thread_id=actual_thread_id)
        await self.db_repo.save(entity=bot_msg)

        return response_text, actual_thread_id