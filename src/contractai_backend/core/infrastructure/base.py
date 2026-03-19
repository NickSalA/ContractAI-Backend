"""BaseRepository: Clase genérica para manejar operaciones CRUD con SQLModel y AsyncSession."""
from collections.abc import Sequence
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..application.base import BaseRepository


class PostgresBaseRepository[T](BaseRepository[T]):
    def __init__(self, session: AsyncSession, model: type[T]):
        """Receives the SQLModel table class and the database session.

        Args:
        - model: Class that represents the database table (Infra)
        - session: Database session for executing queries
        .
        """
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> T | None:
        """Obtiene una entidad por su ID. Devuelve None si no existe."""
        query = select(self.model).where(self.model.id == id)
        result = await self.session.exec(query)
        return result.first()

    async def save(self, entity: T) -> T:
        """Crea un nuevo registro en la base de datos a partir de la entidad. Devuelve la entidad creada con su ID asignado."""
        obj = self.model(**entity.dict(exclude_unset=True))
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_all(self, filters: dict[str, Any] | None = None) -> Sequence[T]:
        """Lista entidades, opcionalmente filtrando por campos específicos."""
        query = select(self.model)
        if filters:
            for field, value in filters.items():
                query = query.where(getattr(self.model, field) == value)
        result = await self.session.exec(query)
        return result.all()

    async def update(self, entity: T) -> T:
        """Actualiza el registro existente con los datos de la entidad. Devuelve la entidad actualizada."""
        db_merged = await self.session.merge(entity)
        await self.session.commit()
        await self.session.refresh(db_merged)
        return db_merged

    async def delete(self, obj_id: int) -> bool:
        """Elimina el registro y devuelve True si tuvo éxito."""
        db_obj = await self.get_by_id(obj_id)
        if not db_obj:
            raise ValueError(f"Registro con ID {obj_id} no encontrado")

        await self.session.delete(db_obj)
        await self.session.commit()
        return True
