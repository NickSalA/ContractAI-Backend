"""Dependency Injection para el módulo de documentos."""

from typing import Annotated

from fastapi import Depends
from qdrant_client import AsyncQdrantClient, QdrantClient
from sqlmodel.ext.asyncio.session import AsyncSession

from ....shared.database import get_aclient, get_client, get_session
from ..application.repositories import DocumentRepository
from ..application.services import DocumentService
from ..infrastructure import LlamaIndexQdrantRepository, LlamaParseExtractor, SQLModelDocumentRepository, SupabaseStorageRepository

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AsyncQdrantDep = Annotated[AsyncQdrantClient, Depends(get_aclient)]
SyncQdrantDep = Annotated[QdrantClient, Depends(get_client)]


async def get_document_repository(session: SessionDep) -> DocumentRepository:
    """Construye un repositorio SQL liviano para endpoints de lectura."""
    return SQLModelDocumentRepository(session=session)


DocumentRepoDep = Annotated[DocumentRepository, Depends(get_document_repository)]


async def get_document_service(sql_repo: DocumentRepoDep, async_qdrant: AsyncQdrantDep, sync_qdrant: SyncQdrantDep) -> DocumentService:
    """Fábrica que construye el DocumentService inyectándole la infraestructura real.

    FastAPI ejecutará esto automáticamente cada vez que un endpoint lo pida.
    """
    extractor = LlamaParseExtractor()
    vector_repo = LlamaIndexQdrantRepository(async_client=async_qdrant, sync_client=sync_qdrant)
    storage_repo = SupabaseStorageRepository()

    # B. Se las inyectamos al servicio a través de su constructor (El "Qué")
    return DocumentService(
        sql_repo=sql_repo,
        vector_repo=vector_repo,
        extractor=extractor,
        storage_repo=storage_repo,
    )
