from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from contractai_backend.shared.config import settings
from contractai_backend.modules.chatbot.infrastructure.agent.state import AgentState

def call_model(state: AgentState):
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL_NAME,
        api_key=settings.GEMINI_API_KEY,
        temperature=settings.MODEL_TEMPERATURE
    )
    response = llm.invoke(state["messages"])
    return {"messages": response}

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_edge(START, "agent")
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)