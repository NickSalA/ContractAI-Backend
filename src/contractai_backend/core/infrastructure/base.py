"""BaseRepository: Clase genérica para manejar operaciones CRUD con SQLModel y AsyncSession."""
from typing import Any, Generic, Sequence, Type, TypeVar

from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

M = TypeVar("M", bound=SQLModel)
E = TypeVar("E")

class BaseRepository(Generic[M, E]):
    def __init__(self, model: Type[M], session: AsyncSession):
        """Receives the SQLModel table class and the database session.

        Args:
        - model: Class that represents the database table (Infra)
        - session: Database session for executing queries
        .
        """
        self.model = model
        self.session = session

    async def _get_db_obj(self, obj_id: int) -> M | None:
        """Busca el modelo real de la base de datos."""
        query = select(self.model).where(self.model.id == obj_id)
        result = await self.session.exec(query)
        return result.first()

    async def get_by_id(self, obj_id: int) -> E | None:
        """Obtiene una entidad por su ID. Devuelve None si no existe."""
        db_obj = await self._get_db_obj(obj_id)
        return self.to_entity(db_obj) if db_obj else None

    async def create(self, entity: E) -> E:
        """Crea un nuevo registro en la base de datos a partir de la entidad. Devuelve la entidad creada con su ID asignado."""
        db_obj = self.to_model(entity)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return self.to_entity(db_obj)

    async def list(self, filters: dict[str, Any] = None) -> Sequence[E]:
        """Lista entidades, opcionalmente filtrando por campos específicos."""
        query = select(self.model)
        if filters:
            for field, value in filters.items():
                query = query.where(getattr(self.model, field) == value)
        result = await self.session.exec(query)
        db_objs = result.all()
        return [self.to_entity(db_obj) for db_obj in db_objs]

    async def update(self, entity: E) -> E:
        """Actualiza el registro existente con los datos de la entidad. Devuelve la entidad actualizada."""
        db_obj = self.to_model(entity)
        db_merged = await self.session.merge(db_obj)
        await self.session.flush()
        return self.to_entity(db_merged)

    async def delete(self, obj_id: int) -> bool:
        """Elimina el registro y devuelve True si tuvo éxito."""
        db_obj = await self._get_db_obj(obj_id)
        if not db_obj:
            raise ValueError(f"Registro con ID {obj_id} no encontrado")

        await self.session.delete(db_obj)
        await self.session.flush()
        return True

    def to_entity(self, model: M) -> E:
        """Convierte el modelo de la base de datos a la entidad de dominio."""
        raise NotImplementedError

    def to_model(self, entity: E) -> M:
        """Convierte la entidad de dominio al modelo de la base de datos."""
        raise NotImplementedError
