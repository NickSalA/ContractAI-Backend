"""Herramientas personalizadas para el agente, inyectando dependencias como el repositorio de vectores."""

from langchain_core.tools import Tool

from ...application.repositories.vector_repo import VectorRepository


def build_bc_tool(repo: VectorRepository) -> Tool:
    """Crea la herramienta de búsqueda inyectando el repositorio."""

    def func(query: str):
        raise NotImplementedError("Herramienta estrictamente asíncrona.")

    async def afunc(query: str) -> str:
        return await repo.search_documents(query=query)

    return Tool(
        name="bc_tool",
        description=(
            "Úsala para buscar información en reglamentos, normativas y documentos "
            "oficiales de la universidad. Devuelve fragmentos relevantes de la base "
            "de conocimientos institucional."
        ),
        func=func,
        coroutine=afunc,
    )
