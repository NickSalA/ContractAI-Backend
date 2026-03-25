from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.shared.config import settings
from contractai_backend.shared.infrastructure.database.qdrant import get_aclient
from contractai_backend.shared.infrastructure.database.postgres import get_session
from contractai_backend.modules.chatbot.application.services.chatbot_service import ChatbotService
from contractai_backend.modules.chatbot.application.services.conversation_service import ConversationService
from contractai_backend.modules.chatbot.infrastructure.conversation_repo import ConversationRepository
from contractai_backend.modules.chatbot.infrastructure.agent.adapter import LangGraphGeminiAdapter
from contractai_backend.modules.chatbot.infrastructure.agent.graph import ContractAgentGraph
from contractai_backend.modules.chatbot.infrastructure.agent.llm import get_llm
from contractai_backend.modules.chatbot.infrastructure.agent.tools import build_bc_tool
from contractai_backend.modules.chatbot.infrastructure.qdrant_repo import QdrantVectorRepository

_chatbot_service_instance: ChatbotService | None = None
_db_pool: AsyncConnectionPool | None = None


def get_conversation_service(session: AsyncSession = Depends(get_session)) -> ConversationService:
    repo = ConversationRepository(session=session)
    return ConversationService(repository=repo)


async def init_chatbot_system() -> ChatbotService:
    global _db_pool

    vector_repo = await QdrantVectorRepository.build(
        collection_name=settings.INDEX_NAME,
        client=await get_aclient()
    )

    bc_tool = build_bc_tool(repo=vector_repo)

    _db_pool = AsyncConnectionPool(
        conninfo=settings.CONN_STRING,
        open=False,
        kwargs={"prepare_threshold": 0, "row_factory": dict_row, "autocommit": True}
    )

    await _db_pool.open()

    checkpointer = AsyncPostgresSaver(_db_pool)
    await checkpointer.setup()

    graph_builder = ContractAgentGraph(tools=[bc_tool], llm=get_llm())
    compiled_graph = graph_builder.build_graph(checkpointer=checkpointer)

    llm_provider = LangGraphGeminiAdapter(compiled_graph=compiled_graph)

    return ChatbotService(llm_provider=llm_provider)


async def get_chatbot_service() -> ChatbotService:
    global _chatbot_service_instance
    if _chatbot_service_instance is None:
        _chatbot_service_instance = await init_chatbot_system()

    return _chatbot_service_instance