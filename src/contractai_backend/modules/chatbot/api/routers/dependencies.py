"""Definición de dependencias para los endpoints del chatbot."""

from .....shared.config import settings
from .....shared.infrastructure.database import get_aclient
from ...application.services.chatbot_service import ChatbotService
from ...infrastructure.agent.adapter import LangGraphGeminiAdapter
from ...infrastructure.agent.graph import ContractAgentGraph
from ...infrastructure.agent.llm import get_llm
from ...infrastructure.agent.tools import build_bc_tool
from ...infrastructure.qdrant_repo import QdrantVectorRepository


async def get_chatbot_service() -> ChatbotService:
    """Ensambla todas las capas de la aplicación de adentro hacia afuera."""
    vector_repo: QdrantVectorRepository = await QdrantVectorRepository.build(collection_name=settings.INDEX_NAME, client=await get_aclient())

    bc_tool = build_bc_tool(repo=vector_repo)

    graph_builder = ContractAgentGraph(tools=[bc_tool], llm=get_llm())
    compiled_graph = graph_builder.build_graph()

    llm_provider = LangGraphGeminiAdapter(compiled_graph=compiled_graph)

    return ChatbotService(llm_provider=llm_provider)
