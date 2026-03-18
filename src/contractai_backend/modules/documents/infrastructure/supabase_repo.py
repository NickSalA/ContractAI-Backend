"""Repositorio de Documentos utilizando SQLModel y AsyncSession para Supabase."""

from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.core.infrastructure.base import BaseRepository
from contractai_backend.modules.documents.application.interfaces.document_repo import IDocumentRepository
from contractai_backend.modules.documents.domain.entities import Document
from contractai_backend.modules.documents.domain.value_objs import DocumentPeriod, Money
from contractai_backend.modules.documents.infrastructure.model import DocumentTable


class SupabaseDocumentRepository(BaseRepository[DocumentTable, Document], IDocumentRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(model=DocumentTable, session=session)

    def to_model(self, entity: Document) -> DocumentTable:
        """Convierte una entidad Document a un modelo DocumentTable para la base de datos."""
        return DocumentTable(
            id=entity.id,
            name=entity.name,
            client=entity.client,
            type=entity.type,
            start=entity.period.start,
            end=entity.period.end,
            value=float(entity.value.amount),
            currency=entity.value.currency,
            licenses=entity.licenses,
            state=entity.state
        )

    def to_entity(self, model: DocumentTable) -> Document:
        """Convierte un modelo DocumentTable de la base de datos a una entidad Document."""
        return Document(
            id=model.id,
            name=model.name,
            client=model.client,
            type=model.type,
            period=DocumentPeriod(start=model.start, end=model.end),
            value=Money(amount=model.value, currency=model.currency),
            licenses=model.licenses,
            state=model.state
        )
