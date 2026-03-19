"""Repositorio de Documentos utilizando SQLModel y AsyncSession para Supabase."""

from sqlmodel.ext.asyncio.session import AsyncSession

from ....core.infrastructure.base import PostgresBaseRepository
from ..application.repositories import DocumentRepository
from ..domain import DocumentTable


class SQLModelDocumentRepository(PostgresBaseRepository[DocumentTable], DocumentRepository):
    """Repositorio de Documentos utilizando SQLModel y AsyncSession para Supabase."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=DocumentTable, session=session)

    async def get_by_client_name(self, client_name: str) -> list[DocumentTable]:
        """Obtiene una lista de documentos por el nombre del cliente."""
        query = self.model.__table__.select().where(self.model.client == client_name)
        result = await self.session.exec(query)
        return result.scalars().all()

    async def get_active_documents(self) -> list[DocumentTable]:
        """Obtiene una lista de documentos activos."""
        query = self.model.__table__.select().where(self.model.state == "active")
        result = await self.session.exec(query)
        return result.scalars().all()
