"""BaseTable: Clase base para todas las tablas de la base de datos."""

from sqlmodel import Field, SQLModel


class BaseTable(SQLModel):
    """Todas las tablas de ContractAI heredarán de aquí."""

    id: int = Field(default=None, primary_key=True, index=True)
