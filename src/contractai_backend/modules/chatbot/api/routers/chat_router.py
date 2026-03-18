from fastapi import APIRouter, Depends
from contractai_backend.modules.chatbot.api.schemas import ChatRequest, ChatResponse
from contractai_backend.modules.chatbot.application.use_cases.process_message import ProcessMessageUseCase
from contractai_backend.modules.chatbot.infrastructure.agent.adapter import LangGraphGeminiAdapter
from contractai_backend.modules.chatbot.application.interfaces.llm_provider import ILLMProvider

router = APIRouter()

langgraph_adapter_instance = LangGraphGeminiAdapter()

def get_llm_provider() -> ILLMProvider:
    return langgraph_adapter_instance

def get_process_message_use_case(
    llm_provider: ILLMProvider = Depends(get_llm_provider)
) -> ProcessMessageUseCase:
    return ProcessMessageUseCase(llm_provider=llm_provider)

@router.post("/", response_model=ChatResponse)
def send_chat_message(
    request: ChatRequest,
    use_case: ProcessMessageUseCase = Depends(get_process_message_use_case)
):
    return use_case.execute(request)