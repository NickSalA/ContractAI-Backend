"""Definición de endpoints para el chatbot."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ...application.services.chatbot_service import ChatbotService
from ..schemas import ChatRequest, ChatResponse
from contractai_backend.modules.chatbot.api.dependencies import get_chatbot_service

router = APIRouter()

ChatbotServiceDep = Annotated[ChatbotService, Depends(get_chatbot_service)]


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    service: ChatbotServiceDep,
) -> ChatResponse:
    """Endpoint para enviar un mensaje al chatbot."""
    respuesta, thread_id = await service.process_user_message(message=request.message, thread_id=request.thread_id)
    return ChatResponse(response=respuesta, thread_id=thread_id)
