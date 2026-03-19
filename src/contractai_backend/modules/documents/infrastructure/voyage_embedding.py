"""Configuración de Voyage AI para LlamaIndex."""

from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding

from contractai_backend.shared.config import settings


# TODO: Cambiar en el futuro al modelo de embedding de Voyage AI una vez que esté disponible públicamente.
def configure_embedding() -> None:
    """Configura el modelo de embedding de Voyage AI globalmente para LlamaIndex."""
    try:
        Settings.embed_model = OpenAIEmbedding(
            model_name=settings.VOYAGE_EMBEDDING_MODEL_NAME,
            api_key=settings.VOYAGE_OPENAI_API_KEY,
            embed_batch_size=50,
            dimensions=1536,
        )
    except Exception as e:
        raise ValueError(f"Error al configurar modelo de embeddings Voyage AI: {e}") from e
