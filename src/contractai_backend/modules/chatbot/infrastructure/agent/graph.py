from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage

from .state import AgentState
from .prompts import get_chat_system_prompt
class ContractAgentGraph:
    def __init__(self, tools: list, llm):
        """
        El constructor recibe las herramientas inyectadas desde afuera.
        El grafo no sabe cómo se construyeron, solo las usa.
        """
        self.tools = tools
        self.llm = llm.bind_tools(self.tools)

    async def call_model(self, state: AgentState):
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
