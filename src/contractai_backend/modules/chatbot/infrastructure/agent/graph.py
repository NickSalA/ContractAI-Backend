"""Grafo de estados para el agente conversacional."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .prompts import get_chat_system_prompt
from .state import AgentState


class ContractAgentGraph:
    def __init__(self, tools: list, llm: BaseChatModel):
        """El constructor recibe las herramientas inyectadas desde afuera.

        El grafo no sabe cómo se construyeron, solo las usa.
        """
        self.tools = tools
        self.llm = llm.bind_tools(self.tools)

    async def call_model(self, state: AgentState):
        """Nodo que llama al modelo de lenguaje con el estado actual."""
        system_message = SystemMessage(content=get_chat_system_prompt())
        messages = [system_message] + state["messages"]

        response = await self.llm.ainvoke(messages)
        return {"messages": response}

    def build_graph(self):
        """Construye y compila el grafo usando el estado de la instancia."""
        workflow = StateGraph(AgentState)

        # Agregamos el nodo del agente (nuestro método)
        workflow.add_node("agent", self.call_model)

        # Agregamos el nodo de herramientas (usando las tools inyectadas)
        workflow.add_node("tools", ToolNode(self.tools))

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", tools_condition)
        workflow.add_edge("tools", "agent")

        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
