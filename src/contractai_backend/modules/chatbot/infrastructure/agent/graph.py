from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from contractai_backend.shared.config import settings
from contractai_backend.modules.chatbot.infrastructure.agent.state import AgentState
from contractai_backend.modules.chatbot.infrastructure.agent.prompts import get_chat_system_prompt
from contractai_backend.modules.chatbot.infrastructure.agent.tools import bc_tool

async def call_model(state: AgentState):
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL_NAME,
        api_key=settings.GEMINI_API_KEY,
        temperature=settings.MODEL_TEMPERATURE
    ).bind_tools([bc_tool])

    system_message = SystemMessage(content=get_chat_system_prompt())
    messages = [system_message] + state["messages"]

    response = await llm.ainvoke(messages)
    return {"messages": response}

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode([bc_tool]))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)