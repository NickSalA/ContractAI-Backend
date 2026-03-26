"""Database models for organizations."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlmodel import Field

from contractai_backend.core.domain.base import BaseTable


class OrganizationTable(BaseTable, table=True):
    __tablename__ = "organizations"

    name: str = Field(sa_column=Column("name", String(255), nullable=False, unique=True))
    is_active: bool = Field(default=True, sa_column=Column("is_active", Boolean, nullable=False, default=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column("created_at", DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column("updated_at", DateTime(timezone=True), nullable=False),
    )
