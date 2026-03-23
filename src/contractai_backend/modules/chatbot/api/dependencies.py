from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.shared.config import settings
from contractai_backend.shared.infrastructure.database.postgres import get_session
from contractai_backend.shared.infrastructure.database.qdrant import get_aclient
from contractai_backend.modules.chatbot.application.services.chatbot_service import ChatbotService
from contractai_backend.modules.chatbot.infrastructure.agent.adapter import LangGraphGeminiAdapter
from contractai_backend.modules.chatbot.infrastructure.agent.graph import ContractAgentGraph
from contractai_backend.modules.chatbot.infrastructure.agent.llm import get_llm
from contractai_backend.modules.chatbot.infrastructure.agent.tools import build_bc_tool
from contractai_backend.modules.chatbot.infrastructure.qdrant_repo import QdrantVectorRepository
from contractai_backend.modules.chatbot.infrastructure.postgres_repo import PostgresHistoryRepository


async def get_chatbot_service(
        db_session: AsyncSession = Depends(get_session)
) -> ChatbotService:
    vector_repo: QdrantVectorRepository = await QdrantVectorRepository.build(
        collection_name=settings.INDEX_NAME,
        client=await get_aclient()
    )

    bc_tool = build_bc_tool(repo=vector_repo)

    graph_builder = ContractAgentGraph(tools=[bc_tool], llm=get_llm())
    compiled_graph = graph_builder.build_graph()

    llm_provider = LangGraphGeminiAdapter(compiled_graph=compiled_graph)

    db_repo = PostgresHistoryRepository(session=db_session)

    return ChatbotService(llm_provider=llm_provider, db_repo=db_repo)