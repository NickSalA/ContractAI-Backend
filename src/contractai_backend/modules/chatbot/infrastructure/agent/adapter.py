import random
from langchain_core.messages import HumanMessage
from contractai_backend.modules.chatbot.application.interfaces.llm_provider import ILLMProvider
from contractai_backend.modules.chatbot.infrastructure.agent.graph import build_graph
from contractai_backend.modules.chatbot.infrastructure.agent.tools import get_retrieval_tool


class LangGraphGeminiAdapter(ILLMProvider):
    def __init__(self):
        self.graph = None

    async def _ensure_graph(self):
        if self.graph is None:
            tool = await get_retrieval_tool()
            self.graph = await build_graph(tool)

    async def invoke(self, message: str, thread_id: int | None) -> tuple[str, int]:
        await self._ensure_graph()
        actual_thread_id = thread_id if thread_id is not None else random.randint(10000, 99999)
        config = {"configurable": {"thread_id": str(actual_thread_id)}}

        result = await self.graph.ainvoke({"messages": [HumanMessage(content=message)]}, config=config)
        return result["messages"][-1].content, actual_thread_id