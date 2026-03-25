from datetime import datetime, timezone
from typing import Any

from pydantic import field_validator
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from contractai_backend.core.domain.base import BaseTable

class ConversationTable(BaseTable, table=True):
    __tablename__: str = "conversations"

    id: int | None = Field(default=None, primary_key=True)
    organization_id: int = Field(sa_column=Column("organization_id", Integer, nullable=False))
    user_id: int = Field(sa_column=Column("user_id", Integer, nullable=False))
    title: str = Field(sa_column=Column("title", String, nullable=False))
    content: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column("content", JSONB, nullable=False, server_default='[]'))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column("created_at", DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column("updated_at", DateTime(timezone=True), nullable=False)
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El título de la conversación no puede estar vacío.")
        return v.strip()

    @field_validator("organization_id", "user_id")
    @classmethod
    def validate_positive_ids(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("El ID debe ser un número entero positivo.")
        return v