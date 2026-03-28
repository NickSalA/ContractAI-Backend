"""Service catalog entity for the documents domain."""

from pydantic import field_validator
from sqlalchemy import Column, Integer, String
from sqlmodel import Field

from ....core.domain.base import BaseTable


class ServiceTable(BaseTable, table=True):
    """Represents a service available for contracts."""

    __tablename__: str = "services"

    organization_id: int = Field(sa_column=Column("organization_id", Integer, nullable=False, index=True))
    name: str = Field(sa_column=Column("name", String(255), nullable=False))

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Rejects blank service names."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Service name cannot be empty.")
        return cleaned
