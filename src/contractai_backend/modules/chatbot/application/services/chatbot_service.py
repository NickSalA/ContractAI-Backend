"""Service for handling chatbot logic."""

from ...api.schemas import ConversationCreate
from ...application.repositories.base_llm import ILLMProvider
from ...domain.entities import ConversationTable, Message
from ...domain.exceptions import ConversationNotFoundError
from .conversation_service import ConversationService

LIMIT_TITLE = 30


class ChatbotService:
    def __init__(self, llm_provider: ILLMProvider, conv_service: ConversationService):
        self.llm_provider: ILLMProvider = llm_provider
        self.conv_service: ConversationService = conv_service

    async def process_user_message(self, message: str, thread_id: int | None, current_user) -> tuple[str, int]:
        """Procesa un mensaje del usuario, obtiene la respuesta del LLM y actualiza la conversación en la base de datos."""
        if thread_id is None:
            generated_title: str = message[:LIMIT_TITLE] + "..." if len(message) > LIMIT_TITLE else message
            conv_obj = ConversationCreate(organization_id=current_user.organization_id, user_id=current_user.id, title=generated_title)
            saved_conv: ConversationTable = await self.conv_service.create_conversation(data=conv_obj)
            thread_id: int = saved_conv.id
        response_text, actual_thread_id = await self.llm_provider.invoke(message=message, thread_id=thread_id)

        messages: list[Message] = [
            Message(role="user", content=message).model_dump(mode="json"),
            Message(role="bot", content=response_text).model_dump(mode="json"),
        ]

        updated_conversation: ConversationTable | None = await self.conv_service.append_messages(
            conversation_id=actual_thread_id, new_message=messages
        )

        if not updated_conversation:
            raise ConversationNotFoundError(
                message=f"No se pudo sincronizar el historial. El thread_id {actual_thread_id} no existe en la base de datos."
            )

        return response_text, actual_thread_id
