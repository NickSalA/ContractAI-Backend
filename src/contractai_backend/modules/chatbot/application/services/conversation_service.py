from contractai_backend.modules.chatbot.application.repositories.base_conversation import IConversationRepository
from contractai_backend.modules.chatbot.api.schemas import ConversationCreate, ConversationRead, ConversationList
from contractai_backend.modules.chatbot.domain.entities import ConversationTable

class ConversationService:
    def __init__(self, repository: IConversationRepository):
        self.repository = repository

    async def create_conversation(self, data: ConversationCreate) -> ConversationRead:
        new_conv = ConversationTable(
            organization_id=data.organization_id,
            user_id=data.user_id,
            title=data.title,
            content=[]
        )
        saved_conv = await self.repository.save(new_conv)
        return ConversationRead.model_validate(saved_conv)

    async def get_conversation(self, conversation_id: int) -> ConversationRead | None:
        conversation = await self.repository.get(id=conversation_id)
        if not conversation:
            return None
        return ConversationRead.model_validate(conversation)

    async def list_user_conversations(self, user_id: int) -> list[ConversationList]:
        conversations = await self.repository.get_by_user(user_id)
        return [ConversationList.model_validate(conv) for conv in conversations]

    async def append_messages(self, conversation_id: int, messages: list[dict]) -> ConversationRead | None:
        updated_conv = await self.repository.update_messages(conversation_id, messages)
        if not updated_conv:
            return None
        return ConversationRead.model_validate(updated_conv)