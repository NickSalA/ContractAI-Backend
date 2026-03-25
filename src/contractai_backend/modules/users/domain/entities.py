from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlmodel import Field, SQLModel


class UserRole(StrEnum):
    ADMIN = "admin"
    WORKER = "worker"


class UserTable(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, sa_column=Column("id", Integer, primary_key=True, autoincrement=True))
    organization_id: int = Field(nullable=False)
    supabase_user_id: UUID | None = Field(default=None, nullable=True)
    email: str = Field(sa_column=Column("email", String(255), nullable=False, unique=True, index=True))
    full_name: str | None = Field(default=None, sa_column=Column("full_name", String(255), nullable=True))
    avatar_url: str | None = Field(default=None, sa_column=Column("avatar_url", Text, nullable=True))
    role: UserRole = Field(sa_column=Column("role", String(6), nullable=False, default=UserRole.WORKER))
    is_active: bool = Field(default=True, sa_column=Column("is_active", Boolean, nullable=False, default=True))
    created_at: datetime | None = Field(default=None, sa_column=Column("created_at", DateTime(timezone=True), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column("updated_at", DateTime(timezone=True), nullable=False))
