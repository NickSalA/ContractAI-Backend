"""Service for handling chatbot logic."""

from ...application.repositories.base_llm import ILLMProvider
from ...domain.entities import ConversationTable, Message
from ...domain.exceptions import ConversationNotFoundError
from .conversation_service import ConversationService


class ChatbotService:
    def __init__(self, llm_provider: ILLMProvider):
        self.llm_provider = llm_provider

    async def process_user_message(self, message: str, thread_id: int | None, conversation_service: ConversationService) -> tuple[str, int]:
        """Procesa un mensaje del usuario, obtiene la respuesta del LLM y actualiza la conversación en la base de datos."""
        if thread_id is None:
            conv_obj = ConversationTable(organization_id=0, user_id=0, title="Nueva Conversación", content=[])
            thread_id = conversation_obj.id

        response_text, actual_thread_id = await self.llm_provider.invoke(message=message, thread_id=thread_id)

        messages: list[Message] = [Message(role="user", content=message), Message(role="bot", content=response_text)]

        updated_conversation: ConversationTable | None = await conversation_service.append_messages(
            conversation_id=actual_thread_id, new_message=messages
        )

        if not updated_conversation:
            raise ConversationNotFoundError(
                message=f"No se pudo sincronizar el historial. El thread_id {actual_thread_id} no existe en la base de datos."
            )

        return response_text, actual_thread_id
