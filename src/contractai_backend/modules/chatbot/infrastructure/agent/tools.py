"""Herramientas personalizadas para el agente, inyectando dependencias como el repositorio de vectores."""

from langchain_core.tools import tool

from ...application.repositories.base_vectorial import VectorRepository


def build_bc_tool(repo: VectorRepository):
    """Crea la herramienta de búsqueda inyectando el repositorio."""

    @tool(
        "bc_tool",
        description=(
            "Úsala para buscar información en reglamentos, normativas y documentos "
            "oficiales de la universidad. Devuelve fragmentos relevantes de la base "
            "de conocimientos institucional."
        ),
    )
    async def bc_tool(query: str, limit: int = 5) -> str:
        """Función que se ejecuta cuando el agente llama a esta herramienta."""
        return await repo.search_documents(query=query, limit=limit)

    return bc_tool
