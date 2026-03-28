"""Repositorio de Documentos utilizando SQLModel y AsyncSession para Supabase."""

# pyright: reportArgumentType=false, reportAttributeAccessIssue=false

from collections import defaultdict
from collections.abc import Sequence

from loguru import logger
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ....core.infrastructure.base import PostgresBaseRepository
from ..application.repositories import DocumentCommandRepository, DocumentQueryRepository, ServiceCatalogRepository
from ..domain import DocumentServiceTable, DocumentTable, ServiceTable
from ..domain.exceptions import DocumentDatabaseError, DocumentDatabaseUnavailableError
from ..domain.value_objs import DocumentState


class SQLModelDocumentRepository(
    PostgresBaseRepository[DocumentTable],
    DocumentQueryRepository,
    DocumentCommandRepository,
    ServiceCatalogRepository,
):
    """Repositorio de Documentos utilizando SQLModel y AsyncSession para Supabase."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=DocumentTable, session=session)

    async def get_by_client_name(self, client_name: str) -> Sequence[DocumentTable]:
        """Obtiene los documentos asociados a un cliente."""
        try:
            client_column = DocumentTable.__table__.c.client
            id_column = DocumentTable.__table__.c.id
            query = select(DocumentTable).where(client_column == client_name).order_by(id_column)
            result = await self.session.exec(statement=query)
            return result.all()
        except OperationalError as e:
            raise DocumentDatabaseUnavailableError() from e
        except SQLAlchemyError as e:
            raise DocumentDatabaseError() from e

    async def get_active_documents(self) -> Sequence[DocumentTable]:
        """Obtiene todos los documentos activos."""
        try:
            state_column = DocumentTable.__table__.c.state
            id_column = DocumentTable.__table__.c.id
            query = select(DocumentTable).where(state_column == DocumentState.ACTIVE).order_by(id_column)
            result = await self.session.exec(statement=query)
            return result.all()
        except OperationalError as e:
            raise DocumentDatabaseUnavailableError() from e
        except SQLAlchemyError as e:
            raise DocumentDatabaseError() from e

    async def get_document_services(self, document_id: int) -> Sequence[DocumentServiceTable]:
        """Obtiene los servicios asociados a un documento."""
        try:
            document_id_column = DocumentServiceTable.__table__.c.document_id
            id_column = DocumentServiceTable.__table__.c.id
            query = select(DocumentServiceTable).where(document_id_column == document_id).order_by(id_column)
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
            document_id_column = DocumentServiceTable.__table__.c.document_id
            id_column = DocumentServiceTable.__table__.c.id
            query = select(DocumentServiceTable).where(document_id_column.in_(document_ids)).order_by(document_id_column, id_column)
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
            document_id_column = DocumentServiceTable.__table__.c.document_id
            id_column = DocumentServiceTable.__table__.c.id
            await self.session.exec(delete(DocumentServiceTable).where(document_id_column == document_id))

            if service_items:
                self.session.add_all(service_items)

            await self.session.commit()

            result = await self.session.exec(select(DocumentServiceTable).where(document_id_column == document_id).order_by(id_column))
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
            organization_id_column = ServiceTable.__table__.c.organization_id
            service_id_column = ServiceTable.__table__.c.id
            query = select(ServiceTable).where(organization_id_column == organization_id, service_id_column.in_(service_ids))
            result = await self.session.exec(statement=query)
            return result.all()
        except OperationalError as e:
            raise DocumentDatabaseUnavailableError() from e
        except SQLAlchemyError as e:
            raise DocumentDatabaseError() from e

    async def get_services(self, organization_id: int) -> Sequence[ServiceTable]:
        """Obtiene el catálogo de servicios de una organización."""
        try:
            organization_id_column = ServiceTable.__table__.c.organization_id
            name_column = ServiceTable.__table__.c.name
            id_column = ServiceTable.__table__.c.id
            query = select(ServiceTable).where(organization_id_column == organization_id).order_by(name_column, id_column)
            result = await self.session.exec(statement=query)
            return result.all()
        except OperationalError as e:
            raise DocumentDatabaseUnavailableError() from e
        except SQLAlchemyError as e:
            raise DocumentDatabaseError() from e
