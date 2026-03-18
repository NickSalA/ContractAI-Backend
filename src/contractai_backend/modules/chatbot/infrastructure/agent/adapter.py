import random
from langchain_core.messages import HumanMessage
from contractai_backend.modules.chatbot.application.interfaces.llm_provider import ILLMProvider
from contractai_backend.modules.chatbot.infrastructure.agent.graph import build_graph


class LangGraphGeminiAdapter(ILLMProvider):
    def __init__(self):
        self.graph = build_graph()

    def invoke(self, message: str, thread_id: int | None) -> tuple[str, int]:
        actual_thread_id = thread_id if thread_id is not None else random.randint(10000, 99999)
        config = {"configurable": {"thread_id": str(actual_thread_id)}}
        input_message = HumanMessage(content=message)

        result = self.graph.invoke({"messages": [input_message]}, config=config)
        output_message = result["messages"][-1].content

        return output_message, actual_thread_id