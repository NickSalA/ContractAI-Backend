from langchain.tools.retriever import create_retriever_tool
from app.agents.tools.helpers.retriever_builder import get_retriever # Usamos su helper
from contractai_backend.shared.config import settings

async def get_retrieval_tool():
    # Usamos la lógica de su archivo retriever_tool.py
    retriever = await get_retriever(settings.INDEX_NAME)
    return create_retriever_tool(
        retriever=retriever,
        name="bc_tool",
        description="Úsala para buscar información en reglamentos y normativas oficiales."
    )