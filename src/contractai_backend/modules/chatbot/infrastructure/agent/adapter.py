import random
from langchain_core.messages import HumanMessage
from contractai_backend.modules.chatbot.application.interfaces.llm_provider import ILLMProvider
from contractai_backend.modules.chatbot.infrastructure.agent.graph import build_graph


class LangGraphGeminiAdapter(ILLMProvider):
    def __init__(self):
        self.graph = build_graph()

    async def invoke(self, message: str, thread_id: int | None) -> tuple[str, int]:
        actual_thread_id = thread_id if thread_id is not None else random.randint(10000, 99999)
        config = {"configurable": {"thread_id": str(actual_thread_id)}}

        result = await self.graph.ainvoke({"messages": [HumanMessage(content=message)]}, config=config)

        last_message = result["messages"][-1]
        raw_content = last_message.content

        if isinstance(raw_content, list):
            output_message = "".join(
                [part.get("text", "") for part in raw_content if isinstance(part, dict) and "text" in part])
        else:
            output_message = str(raw_content)

        input_tokens = 0
        output_tokens = 0

        if hasattr(last_message, 'usage_metadata') and last_message.usage_metadata:
            input_tokens = last_message.usage_metadata.get("input_tokens", 0)
            output_tokens = last_message.usage_metadata.get("output_tokens", 0)

        output_message += f"\n\n---\n📊 Tokens de entrada: {input_tokens} | Tokens de salida: {output_tokens}"

        return output_message, actual_thread_id