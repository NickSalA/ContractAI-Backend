"""Grafo de estados para el agente conversacional."""

from functools import partial

from langchain.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import Runnable
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .prompts import get_chat_system_prompt
from .state import AgentState


async def call_model(state: AgentState, llm: Runnable):
    """Nodo que llama al modelo de lenguaje con el estado actual."""
    system_message = SystemMessage(content=get_chat_system_prompt())
    messages = [system_message] + state["messages"]

    response = await llm.ainvoke(messages)
    return {"messages": response}

class ContractAgentGraph:
    def __init__(self, tools: list, llm: BaseChatModel):
        """El constructor recibe las herramientas inyectadas desde afuera.

        El grafo no sabe cómo se construyeron, solo las usa.
        """
        self.tools = tools
        self.llm = llm.bind_tools(self.tools)


    def build_graph(self):
        """Construye y compila el grafo usando el estado de la instancia."""
        workflow = StateGraph(AgentState)
        agent_node = partial(call_model, llm=self.llm)

        # Agregamos el nodo del agente (nuestro método)
        workflow.add_node("agent", agent_node)

        # Agregamos el nodo de herramientas (usando las tools inyectadas)
        workflow.add_node("tools", ToolNode(self.tools))

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", tools_condition)
        workflow.add_edge("tools", "agent")

        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
