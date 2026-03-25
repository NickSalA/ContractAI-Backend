"""Graph definition for the ContractAI chatbot agent."""

from functools import partial

from langchain.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import Runnable
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .prompts import get_chat_system_prompt
from .state import AgentState


async def call_model(state: AgentState, llm: Runnable):
    """Función que llama al modelo LLM, construyendo el mensaje con el prompt del sistema y el historial de mensajes del estado."""
    system_message = SystemMessage(content=get_chat_system_prompt())
    messages = [system_message] + state["messages"]

    response = await llm.ainvoke(messages)
    return {"messages": response}


class ContractAgentGraph:
    def __init__(self, tools: list, llm: BaseChatModel):
        self.tools = tools
        self.llm = llm.bind_tools(self.tools)

    def build_graph(self, checkpointer):
        """Construye el grafo de estados para el agente, definiendo los nodos y las transiciones entre ellos."""
        workflow = StateGraph(AgentState)  # ty:ignore[invalid-argument-type]
        agent_node = partial(call_model, llm=self.llm)

        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", ToolNode(self.tools))

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", tools_condition)
        workflow.add_edge("tools", "agent")

        return workflow.compile(checkpointer=checkpointer)
