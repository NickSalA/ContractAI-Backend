from datetime import datetime, UTC

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.core.infrastructure.base import PostgresBaseRepository
from contractai_backend.modules.users.domain.entities import UserTable


class SQLModelUserRepository(PostgresBaseRepository[UserTable]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=UserTable)

    async def get_by_email(self, email: str) -> UserTable | None:
        query = select(self.model).where(func.lower(self.model.email) == email.strip().lower())
        result = await self.session.exec(query)
        return result.first()

    async def update_fields(self, user: UserTable, **changes) -> UserTable:
        for field, value in changes.items():
            setattr(user, field, value)
        user.updated_at = datetime.now(UTC)
        return await self.update(user)
