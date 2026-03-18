from contractai_backend.modules.chatbot.api.schemas import ChatRequest, ChatResponse
from contractai_backend.modules.chatbot.application.interfaces.llm_provider import ILLMProvider


class ProcessMessageUseCase:
    def __init__(self, llm_provider: ILLMProvider):
        self.llm_provider = llm_provider

    def execute(self, request: ChatRequest) -> ChatResponse:
        response_text, thread_id = self.llm_provider.invoke(
            message=request.message,
            thread_id=request.thread_id
        )

        return ChatResponse(
            response=response_text,
            thread_id=thread_id
        )