"""Repositorio de Plantillas utilizando SQLModel y AsyncSession para PostgreSQL."""
from collections.abc import Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ....core.infrastructure.base import PostgresBaseRepository
from ..application.repositories.base_relational import ITemplateRepository
from ..domain.entities import TemplateTable


class SQLModelTemplateRepository(PostgresBaseRepository[TemplateTable], ITemplateRepository):

    def __init__(self, session: AsyncSession):
            super().__init__(model=TemplateTable, session=session)

    async def get_template_by_id(self, template_id: int, organization_id: int | None) -> TemplateTable | None:
        """Obtiene la plantilla validando que pertenezca a la organización."""
        query = select(self.model).where(self.model.id == template_id)
        if organization_id is not None:
            query = query.where(self.model.organization_id == organization_id)
        else:
            query = query.where(self.model.organization_id is None)
        result = await self.session.exec(statement=query)
        return result.first()

    async def list_by_organization(self, organization_id: int) -> Sequence[TemplateTable]:
        """Lista las plantillas de una organización."""
        query = select(self.model).where(self.model.organization_id == organization_id)
        result = await self.session.exec(statement=query)
        return result.all()
