"""Database model for documents with SQLModel."""

from datetime import UTC, date, datetime

from pydantic import ValidationInfo, field_validator
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.dialects.postgresql import ENUM
from sqlmodel import Field

from ....core.domain.base import BaseTable
from .value_objs import DocumentState, DocumentType

CURRENCY_CODE_LENGTH = 3


class DocumentTable(BaseTable, table=True):
    __tablename__: str = "documents"

    organization_id: int = Field(sa_column=Column("organization_id", nullable=False, index=True))
    name: str = Field(sa_column=Column("name", nullable=False))
    client: str = Field(sa_column=Column("client", nullable=False))
    type: DocumentType = Field(sa_column=Column("type", ENUM(DocumentType, name="document_type"), nullable=False))
    start_date: date = Field(sa_column=Column("start_date", nullable=False))
    end_date: date = Field(sa_column=Column("end_date", nullable=False))
    value: float = Field(sa_column=Column("value", nullable=False))
    currency: str = Field(sa_column=Column("currency", nullable=False))
    licenses: int = Field(sa_column=Column("licenses", type_=Integer, nullable=False))
    state: DocumentState = Field(default=DocumentState.ACTIVE, sa_column=Column("state", ENUM(DocumentState, name="document_state"), nullable=False))
    file_path: str | None = Field(default=None, sa_column=Column("file_path", nullable=True))
    file_name: str | None = Field(default=None, sa_column=Column("file_name", nullable=True))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=Column("created_at", DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=Column("updated_at", DateTime(timezone=True), nullable=False))

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, end_date: date, info: ValidationInfo) -> date:
        """Valida que la fecha de fin no sea anterior a la fecha de inicio."""
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("End date cannot be earlier than start date.")
        return end_date

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: float) -> float:
        """Valida que el valor monetario sea positivo."""
        if value < 0:
            raise ValueError("Value must be a positive number.")
        return value

    @field_validator("licenses")
    @classmethod
    def validate_licenses(cls, licenses: int) -> int:
        """Valida que el número de licencias sea un entero no negativo."""
        if licenses < 0:
            raise ValueError("Licenses must be a non-negative integer.")
        return licenses

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, currency: str) -> str:
        """Valida que el código de moneda sea un string de 3 caracteres."""
        if len(currency) != CURRENCY_CODE_LENGTH:
            raise ValueError(f"Currency code must be a {CURRENCY_CODE_LENGTH}-letter string.")
        if currency != currency.upper():
            raise ValueError("Currency code must be uppercase.")
        return currency
