"""Database models for the documents module."""

from datetime import UTC, date, datetime
from typing import Any

from pydantic import ValidationInfo, field_validator
from sqlalchemy import Column, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlmodel import Field

from ....core.domain.base import BaseTable
from .value_objs import CurrencyType, DocumentState, DocumentType


class DocumentTable(BaseTable, table=True):
    __tablename__: str = "documents"

    organization_id: int = Field(sa_column=Column("organization_id", Integer, nullable=False, index=True))
    name: str = Field(sa_column=Column("name", String(255), nullable=False))
    client: str = Field(sa_column=Column("client", String(255), nullable=False))
    type: DocumentType = Field(sa_column=Column("type", ENUM(DocumentType, name="document_type"), nullable=False))
    start_date: date = Field(sa_column=Column("start_date", Date, nullable=False))
    end_date: date = Field(sa_column=Column("end_date", Date, nullable=False))
    form_data: dict[str, Any] = Field(default_factory=dict, sa_column=Column("form_data", JSONB, nullable=False))
    state: DocumentState = Field(
        default=DocumentState.ACTIVE,
        sa_column=Column("state", ENUM(DocumentState, name="document_state"), nullable=False),
    )
    file_path: str | None = Field(default=None, sa_column=Column("file_path", Text, nullable=True))
    file_name: str | None = Field(default=None, sa_column=Column("file_name", Text, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column("created_at", DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column("updated_at", DateTime(timezone=True), nullable=False),
    )

    @field_validator("name", "client")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """Valida textos obligatorios no vacíos."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty.")
        return cleaned

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, end_date: date, info: ValidationInfo) -> date:
        """Valida que la fecha de fin no sea anterior a la fecha de inicio."""
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("End date cannot be earlier than start date.")
        return end_date

    @field_validator("form_data")
    @classmethod
    def validate_form_data(cls, form_data: dict[str, Any]) -> dict[str, Any]:
        """Valida que los datos estructurados sean un objeto JSON."""
        if not isinstance(form_data, dict):
            raise ValueError("form_data must be a JSON object.")
        return form_data


class ServiceTable(BaseTable, table=True):
    __tablename__: str = "services"

    organization_id: int = Field(sa_column=Column("organization_id", Integer, nullable=False, index=True))
    name: str = Field(sa_column=Column("name", String(255), nullable=False))

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Service name cannot be empty.")
        return cleaned


class DocumentServiceTable(BaseTable, table=True):
    __tablename__: str = "documents_services"

    document_id: int = Field(sa_column=Column("document_id", Integer, nullable=False, index=True))
    service_id: int = Field(sa_column=Column("service_id", Integer, nullable=False, index=True))
    description: str | None = Field(default=None, sa_column=Column("description", Text, nullable=True))
    value: float = Field(sa_column=Column("value", Float, nullable=False))
    currency: CurrencyType = Field(sa_column=Column("currency", ENUM(CurrencyType, name="currency_type"), nullable=False))
    start_date: date = Field(sa_column=Column("start_date", Date, nullable=False))
    end_date: date = Field(sa_column=Column("end_date", Date, nullable=False))

    @field_validator("document_id", "service_id")
    @classmethod
    def validate_positive_ids(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("ID must be a positive integer.")
        return value

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Value must be a positive number.")
        return value

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, end_date: date, info: ValidationInfo) -> date:
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("End date cannot be earlier than start date.")
        return end_date
