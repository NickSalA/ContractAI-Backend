from contractai_backend.modules.chatbot.application.repositories.base_llm import ILLMProvider
from contractai_backend.modules.chatbot.application.services.conversation_service import ConversationService
from contractai_backend.modules.chatbot.domain.exceptions import ConversationNotFoundError


class ChatbotService:
    def __init__(self, llm_provider: ILLMProvider):
        self.llm_provider = llm_provider

    async def process_user_message(self, message: str, thread_id: int, conversation_service: ConversationService) -> \
    tuple[str, int]:
        response_text, actual_thread_id = await self.llm_provider.invoke(
            message=message,
            thread_id=thread_id
        )

        messages_to_append = [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response_text}
        ]

        updated_conversation = await conversation_service.append_messages(
            conversation_id=actual_thread_id,
            messages=messages_to_append
        )

        if not updated_conversation:
            raise ConversationNotFoundError(
                message=f"No se pudo sincronizar el historial. El thread_id {actual_thread_id} no existe en la base de datos.")

        return response_text, actual_thread_id