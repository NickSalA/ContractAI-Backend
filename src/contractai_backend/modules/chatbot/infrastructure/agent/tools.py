from langchain_core.tools import tool
from contractai_backend.modules.chatbot.infrastructure.qdrant_repo import ChatbotQdrantRepository


@tool
def bc_tool(query: str) -> str:
    """Úsala para buscar información en reglamentos y normativas oficiales.
    Devuelve fragmentos relevantes de la base de conocimientos institucional."""

    repo = ChatbotQdrantRepository()
    return repo.search_documents(query=query, limit=5)