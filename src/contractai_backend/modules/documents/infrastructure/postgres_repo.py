"""Repositorio de Documentos utilizando SQLModel y AsyncSession para Supabase."""

from collections import defaultdict
from collections.abc import Sequence

from loguru import logger
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ....core.infrastructure.base import PostgresBaseRepository
from ..application.repositories import DocumentRepository
from ..domain import DocumentServiceTable, DocumentTable, ServiceTable
from ..domain.exceptions import DocumentDatabaseError, DocumentDatabaseUnavailableError


class SQLModelDocumentRepository(PostgresBaseRepository[DocumentTable], DocumentRepository):
    """Repositorio de Documentos utilizando SQLModel y AsyncSession para Supabase."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=DocumentTable, session=session)

    async def get_document_services(self, document_id: int) -> Sequence[DocumentServiceTable]:
        """Obtiene los servicios asociados a un documento."""
        try:
            query = select(DocumentServiceTable).where(DocumentServiceTable.document_id == document_id).order_by(DocumentServiceTable.id)
            result = await self.session.exec(statement=query)
            return result.all()
        except OperationalError as e:
            raise DocumentDatabaseUnavailableError() from e
        except SQLAlchemyError as e:
            raise DocumentDatabaseError() from e

    async def get_document_services_by_document_ids(self, document_ids: Sequence[int]) -> dict[int, Sequence[DocumentServiceTable]]:
        """Obtiene los servicios asociados a múltiples documentos en una sola consulta."""
        if not document_ids:
            return {}

        try:
            query = (
                select(DocumentServiceTable)
                .where(DocumentServiceTable.document_id.in_(document_ids))
                .order_by(DocumentServiceTable.document_id, DocumentServiceTable.id)
            )
            result = await self.session.exec(statement=query)
            grouped_services: defaultdict[int, list[DocumentServiceTable]] = defaultdict(list)
            for service_item in result.all():
                grouped_services[service_item.document_id].append(service_item)
            return dict(grouped_services)
        except OperationalError as e:
            raise DocumentDatabaseUnavailableError() from e
        except SQLAlchemyError as e:
            raise DocumentDatabaseError() from e

    async def replace_document_services(self, document_id: int, service_items: Sequence[DocumentServiceTable]) -> Sequence[DocumentServiceTable]:
        """Reemplaza el conjunto de servicios asociados a un documento."""
        try:
            await self.session.exec(delete(DocumentServiceTable).where(DocumentServiceTable.document_id == document_id))

            if service_items:
                self.session.add_all(service_items)

            await self.session.commit()

            result = await self.session.exec(
                select(DocumentServiceTable).where(DocumentServiceTable.document_id == document_id).order_by(DocumentServiceTable.id)
            )
            return result.all()
        except OperationalError as e:
            await self.session.rollback()
            logger.debug(f"OperationalError replacing services for document {document_id}: {e}")
            raise DocumentDatabaseUnavailableError() from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.debug(f"SQLAlchemyError replacing services for document {document_id}: {e}")
            raise DocumentDatabaseError() from e

    async def get_services_by_ids(self, organization_id: int, service_ids: Sequence[int]) -> Sequence[ServiceTable]:
        """Obtiene los servicios existentes por sus IDs dentro de una organización."""
        if not service_ids:
            return []

        try:
            query = select(ServiceTable).where(ServiceTable.organization_id == organization_id, ServiceTable.id.in_(service_ids))
            result = await self.session.exec(statement=query)
            return result.all()
        except OperationalError as e:
            raise DocumentDatabaseUnavailableError() from e
        except SQLAlchemyError as e:
            raise DocumentDatabaseError() from e

    async def get_services(self, organization_id: int) -> Sequence[ServiceTable]:
        """Obtiene el catálogo de servicios de una organización."""
        try:
            query = select(ServiceTable).where(ServiceTable.organization_id == organization_id).order_by(ServiceTable.name, ServiceTable.id)
            result = await self.session.exec(statement=query)
            return result.all()
        except OperationalError as e:
            raise DocumentDatabaseUnavailableError() from e
        except SQLAlchemyError as e:
            raise DocumentDatabaseError() from e
