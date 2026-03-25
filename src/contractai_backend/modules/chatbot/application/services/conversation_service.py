"""Service for handling conversation logic."""

from ...api.schemas import ConversationCreate, ConversationList, ConversationRead
from ...domain.entities import ConversationTable, Message
from ..repositories.base_conversation import IConversationRepository


class ConversationService:
    def __init__(self, repository: IConversationRepository):
        self.repository = repository

    async def create_conversation(self, data: ConversationCreate) -> ConversationTable:
        """Crea una nueva conversación en la base de datos a partir de los datos proporcionados."""
        new_conv = ConversationTable(organization_id=data.organization_id, user_id=data.user_id, title=data.title, content=[])
        saved_conv = await self.repository.save(new_conv)
        return ConversationTable.model_validate(obj=saved_conv)

    async def get_conversation(self, conversation_id: int) -> ConversationRead | None:
        """Obtiene una conversación por su ID. Devuelve None si no existe."""
        conversation = await self.repository.get_by_id(id=conversation_id)
        if not conversation:
            return None
        return ConversationRead.model_validate(conversation)

    async def list_user_conversations(self, user_id: int) -> list[ConversationList]:
        """Obtiene una lista de conversaciones asociadas a un usuario específico."""
        conversations = await self.repository.get_by_user(user_id)
        return [ConversationList.model_validate(conv) for conv in conversations]

    async def append_messages(self, conversation_id: int, new_message: list[Message]) -> ConversationTable | None:
        """Agrega nuevos mensajes al contenido de una conversación existente. Devuelve la conversación actualizada o None si no se encuentra."""
        updated_conv: ConversationTable | None = await self.repository.update_messages(conversation_id, new_message)
        if not updated_conv:
            return None
        return ConversationTable.model_validate(obj=updated_conv)
