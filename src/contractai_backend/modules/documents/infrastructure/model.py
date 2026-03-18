"""Database model for documents with SQLModel."""
from datetime import date

from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import ENUM
from sqlmodel import Field, SQLModel

from contractai_backend.modules.documents.domain import DocumentState, DocumentType


class DocumentTable(SQLModel, table=True):
    __tablename__ = "documents"

    id: int = Field(default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True))
    name: str = Field(sa_column=Column("name", nullable=False))
    client: str = Field(sa_column=Column("client", nullable=False))
    type: DocumentType = Field(sa_column=Column("type", ENUM(DocumentType, name="document_type"), nullable=False))
    start: date = Field(sa_column=Column("start_date", nullable=False))
    end: date = Field(sa_column=Column("end_date", nullable=False))
    value: float = Field(sa_column=Column("value", nullable=False))
    currency: str = Field(sa_column=Column("currency", nullable=False))
    licenses: int = Field(sa_column=Column("licenses", type_=Integer, nullable=False))
    state: DocumentState = Field(sa_column=Column("state", ENUM(DocumentState, name="document_state"), nullable=False))
