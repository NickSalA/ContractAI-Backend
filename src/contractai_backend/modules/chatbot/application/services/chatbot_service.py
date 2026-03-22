"""ChatbotService es la capa de servicios que contiene la lógica de negocio para procesar mensajes del chatbot."""

from ...application.repositories.llm_provider import ILLMProvider


class ChatbotService:
    def __init__(self, llm_provider: ILLMProvider): #, db_repo: IDatabaseRepository):
        self.llm_provider = llm_provider
        # self.db_repo = db_repo

    async def process_user_message(self, message: str, thread_id: int | None = None) -> tuple[str, int]:
        """Procesa un mensaje del usuario, interactuando con el LLM y opcionalmente guardando el historial en Postgres."""
        # 1. Opcional: Podrías guardar el mensaje del usuario en Postgres aquí
        # await self.db_repo.save_message(role="user", content=message, thread_id=thread_id)

        # 2. Llamamos al LLM (El servicio NO SABE que esto usa LangGraph o Gemini)
        response_text, actual_thread_id = await self.llm_provider.invoke(
            message=message,
            thread_id=thread_id
        )

        # 3. Opcional: Podrías guardar la respuesta del bot en Postgres aquí
        # await self.db_repo.save_message(role="assistant", content=response_text, thread_id=actual_thread_id)

        # 4. Formatear la respuesta para el Router
        return response_text, actual_thread_id
