"""Schemas para la API del chatbot."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message to the chatbot.", examples=["Hola, ¿cómo estás?"])
    thread_id: int | None = Field(default=None, description="ID de la conversación.", examples=[12])

class ChatResponse(BaseModel):
    response: str = Field(..., description="The chatbot's response to the user's message.", examples=["¡Hola! Estoy bien..."])
    thread_id: int = Field(..., description="ID de la conversación.", examples=[12])
