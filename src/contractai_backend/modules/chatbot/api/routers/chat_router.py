from typing import Annotated
from fastapi import APIRouter, Depends

from contractai_backend.modules.chatbot.api.schemas import ChatRequest, ChatResponse
from contractai_backend.modules.chatbot.application.services.chatbot_service import ChatbotService
from contractai_backend.modules.chatbot.application.services.conversation_service import ConversationService
from contractai_backend.modules.chatbot.api.dependencies import get_chatbot_service, get_conversation_service
from contractai_backend.modules.chatbot.domain.exceptions import ChatbotValidationError

router = APIRouter()

ChatbotServiceDep = Annotated[ChatbotService, Depends(get_chatbot_service)]
ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
        request: ChatRequest,
        service: ChatbotServiceDep,
        conversation_service: ConversationServiceDep
) -> ChatResponse:
    if not request.message or not request.message.strip():
        raise ChatbotValidationError(message="El mensaje no puede estar vacío.")

    if not request.thread_id:
        raise ChatbotValidationError(message="Se requiere un thread_id válido.")

    respuesta, thread_id = await service.process_user_message(
        message=request.message.strip(),
        thread_id=request.thread_id,
        conversation_service=conversation_service
    )

    return ChatResponse(response=respuesta, thread_id=thread_id)
