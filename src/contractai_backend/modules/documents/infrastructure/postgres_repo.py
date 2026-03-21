"""Repositorio de Documentos utilizando SQLModel y AsyncSession para Supabase."""

from collections.abc import Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ....core.infrastructure.base import PostgresBaseRepository
from ..application.repositories import DocumentRepository
from ..domain import DocumentState, DocumentTable


class SQLModelDocumentRepository(PostgresBaseRepository[DocumentTable], DocumentRepository):
    """Repositorio de Documentos utilizando SQLModel y AsyncSession para Supabase."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=DocumentTable, session=session)

    async def get_by_client_name(self, client_name: str) -> Sequence[DocumentTable]:
        """Obtiene una lista de documentos por el nombre del cliente."""
        query = select(self.model).where(self.model.client == client_name)
        result = await self.session.exec(query)
        return result.all()

    async def get_active_documents(self) -> Sequence[DocumentTable]:
        """Obtiene una lista de documentos activos."""
        query = select(self.model).where(self.model.state == DocumentState.ACTIVE)
        result = await self.session.exec(query)
        return result.all()
