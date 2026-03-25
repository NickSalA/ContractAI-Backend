from typing import Annotated
from fastapi import APIRouter, Depends

from contractai_backend.modules.chatbot.api.schemas import ConversationCreate, ConversationRead, ConversationList
from contractai_backend.modules.chatbot.application.services.conversation_service import ConversationService
from contractai_backend.modules.chatbot.api.dependencies import get_conversation_service
from contractai_backend.modules.chatbot.domain.exceptions import ConversationNotFoundError

router = APIRouter()
ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]

@router.post("/", response_model=ConversationRead)
async def create_new_conversation(request: ConversationCreate, service: ConversationServiceDep):
    return await service.create_conversation(request)

@router.get("/user/{user_id}", response_model=list[ConversationList])
async def list_my_conversations(user_id: int, service: ConversationServiceDep):
    return await service.list_user_conversations(user_id)

@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_single_conversation(conversation_id: int, service: ConversationServiceDep):
    conversation = await service.get_conversation(conversation_id)
    if not conversation:
        raise ConversationNotFoundError()
    return conversation