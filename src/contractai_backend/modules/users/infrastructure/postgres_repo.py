"""Módulo de repositorio de usuarios utilizando SQLModel y PostgreSQL."""

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.core.infrastructure.base import PostgresBaseRepository
from contractai_backend.modules.users.application.repositories.user_repo import IUserRepository
from contractai_backend.modules.users.domain.entities import UserTable


class SQLModelUserRepository(PostgresBaseRepository[UserTable], IUserRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=UserTable)

    async def get_by_email(self, email: str) -> UserTable | None:
        """Obtiene un usuario por su email. Devuelve None si no se encuentra."""
        query = select(self.model).where(func.lower(self.model.email) == email.strip().lower())
        result = await self.session.exec(query)
        return result.first()
