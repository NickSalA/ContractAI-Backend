"""Routes related to conversations."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ...api.dependencies import get_conversation_service
from ...api.schemas import ConversationList, ConversationRead
from ...application import ConversationService
from ...domain import ConversationNotFoundError

router = APIRouter()
ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]


@router.get(path="/user/{user_id}", response_model=list[ConversationList])
async def list_my_conversations(user_id: int, service: ConversationServiceDep):
    """Endpoint para listar las conversaciones de un usuario específico."""
    return await service.list_user_conversations(user_id)


@router.get(path="/{conversation_id}", response_model=ConversationRead)
async def get_single_conversation(conversation_id: int, service: ConversationServiceDep):
    """Endpoint para obtener una conversación específica."""
    conversation: ConversationRead | None = await service.get_conversation(conversation_id)
    if not conversation:
        raise ConversationNotFoundError()
    return conversation
