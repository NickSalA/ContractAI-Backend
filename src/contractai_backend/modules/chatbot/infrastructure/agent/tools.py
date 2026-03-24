from langchain_core.tools import tool
from ...application.repositories.base_vectorial import VectorRepository

def build_bc_tool(repo: VectorRepository):

    @tool(
        "bc_tool",
        description=(
            "Usala obligatoriamente para buscar informacion en contratos corporativos, "
            "anexos, acuerdos comerciales, SLAs y documentos legales. Devuelve fragmentos "
            "relevantes de la base de conocimientos contractual de la empresa."
        ),
    )
    async def bc_tool(query: str, limit: int = 5) -> str:
        return await repo.search_documents(query=query, limit=limit)

    return bc_tool