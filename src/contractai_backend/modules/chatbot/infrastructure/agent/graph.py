from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver  # Seguimos con memory hasta que migres a Postgres
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from contractai_backend.shared.config import settings
from contractai_backend.modules.chatbot.infrastructure.agent.state import AgentState
from contractai_backend.modules.chatbot.infrastructure.agent.prompts import get_chat_system_prompt


async def call_model(state: AgentState, bc_tool_instance):
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL_NAME,
        api_key=settings.GEMINI_API_KEY,
        temperature=settings.MODEL_TEMPERATURE
    ).bind_tools([bc_tool_instance])

    # Inyectamos el prompt institucional de tu amigo
    system_message = SystemMessage(content=get_chat_system_prompt())
    messages = [system_message] + state["messages"]

    response = llm.invoke(messages)
    return {"messages": response}


async def build_graph(bc_tool_instance):
    workflow = StateGraph(AgentState)

    # Pasamos la tool a la función del nodo
    workflow.add_node("agent", lambda state: call_model(state, bc_tool_instance))
    workflow.add_node("tools", ToolNode([bc_tool_instance]))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)