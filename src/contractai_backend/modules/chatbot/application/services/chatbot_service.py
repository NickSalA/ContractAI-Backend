import random
from contractai_backend.modules.chatbot.application.repositories.base_llm import ILLMProvider


class ChatbotService:
    def __init__(self, llm_provider: ILLMProvider):
        self.llm_provider = llm_provider

    async def process_user_message(self, message: str, thread_id: int | None = None) -> tuple[str, int]:
        current_thread_id = thread_id if thread_id is not None else random.randint(10000, 99999)

        response_text, actual_thread_id = await self.llm_provider.invoke(
            message=message,
            thread_id=current_thread_id
        )

        return response_text, actual_thread_id