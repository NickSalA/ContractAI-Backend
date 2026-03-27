"""Tools personalizados para el agente de chatbot, integrando la búsqueda en la base de conocimientos contractual."""

from langchain_core.tools import tool

from ...application.repositories import VectorRepository


def build_bc_tool(repo: VectorRepository):
    """Construye una herramienta para el agente, que utiliza el repositorio vectorial para buscar información en la base de conocimientos."""

    @tool(
        name_or_callable="bc_tool",
        description=(
                "Usala obligatoriamente para buscar informacion en contratos corporativos, "
                "anexos, acuerdos comerciales, SLAs y documentos legales. Devuelve fragmentos "
                "relevantes de la base de conocimientos contractual de la empresa."
        ),
    )
    async def bc_tool(query: str, limit: int = 5) -> str:
        return await repo.search_documents(query=query, limit=limit)

    return bc_tool
