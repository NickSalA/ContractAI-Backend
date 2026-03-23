"""Database model for chatbot messages with SQLModel."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlmodel import Field

from contractai_backend.core.domain.base import BaseTable

class ChatMessageTable(BaseTable, table=True):
    __tablename__: str = "chat_messages"

    thread_id: int | None = Field(default=None, sa_column=Column("thread_id", Integer, index=True, nullable=True))
    role: str = Field(sa_column=Column("role", String(50), nullable=False))
    content: str = Field(sa_column=Column("content", Text, nullable=False))
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column("timestamp", DateTime(timezone=True), nullable=False)
    )