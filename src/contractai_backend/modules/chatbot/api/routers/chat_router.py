"""Definición de endpoints para el chatbot."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ...application.repositories.llm_provider import ILLMProvider
from ..schemas import ChatRequest, ChatResponse
from .dependencies import get_llm_provider

router = APIRouter()

LlmProviderDep = Annotated[ILLMProvider, Depends(get_llm_provider)]


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    provider: LlmProviderDep,
) -> ChatResponse:
    """Endpoint para enviar un mensaje al chatbot."""
    respuesta, thread_id = await provider.invoke(request.message, request.thread_id)
    return ChatResponse(response=respuesta, thread_id=thread_id)
