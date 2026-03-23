"""Adaptador para Google Generative AI (Gemini)."""

from langchain_google_genai import ChatGoogleGenerativeAI

from .....shared.config import settings


def get_llm() -> ChatGoogleGenerativeAI:
    """Obtener el LLM de Google Generative AI.

    Returns:
        ChatGoogleGenerativeAI: Instancia del modelo de lenguaje.

    Raises:
        ValueError: Si hay error al inicializar el modelo.
    """
    try:
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL_NAME,
            api_key=settings.GEMINI_API_KEY,
            temperature=settings.MODEL_TEMPERATURE,
            max_retries=0
        )
    except Exception as e:
        raise ValueError(
            f"Error al inicializar el modelo Gemini: {e}"
        ) from e
