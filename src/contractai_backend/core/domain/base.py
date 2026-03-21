""""BaseTable: Clase base para todas las tablas de la base de datos."""
from sqlmodel import Column, Field, Integer, SQLModel


class BaseTable(SQLModel):
    """Todas las tablas de ContractAI heredarán de aquí."""
    id: int = Field(default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True))
