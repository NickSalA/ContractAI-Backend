"""Dependency Injection para el módulo de documentos."""

from typing import Annotated

import httpx
from fastapi import Depends
from qdrant_client import AsyncQdrantClient, QdrantClient
from sqlmodel.ext.asyncio.session import AsyncSession

from ....shared.infrastructure.database import get_aclient, get_client, get_session
from ....shared.infrastructure.http import get_http_client
from ..application.repositories import DocumentExtractor, DocumentRepository, DocumentStorageRepository, VectorRepository
from ..application.services import DocumentService
from ..infrastructure import LlamaIndexQdrantRepository, LlamaParseExtractor, SQLModelDocumentRepository, SupabaseStorageRepository

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AsyncQdrantDep = Annotated[AsyncQdrantClient, Depends(get_aclient)]
SyncQdrantDep = Annotated[QdrantClient, Depends(get_client)]


async def get_document_repository(session: SessionDep) -> DocumentRepository:
    """Construye un repositorio SQL liviano para endpoints de lectura."""
    return SQLModelDocumentRepository(session=session)


async def get_vector_repository(async_qdrant: AsyncQdrantDep, sync_qdrant: SyncQdrantDep) -> VectorRepository:
    """Construye un repositorio de vectores Qdrant."""
    return LlamaIndexQdrantRepository(async_client=async_qdrant, sync_client=sync_qdrant)


async def get_extractor() -> DocumentExtractor:
    """Construye un extractor de datos basado en LlamaParse."""
    return LlamaParseExtractor()


async def get_storage_repository(client: Annotated[httpx.AsyncClient, Depends(get_http_client)]) -> DocumentStorageRepository:
    """Construye un repositorio de almacenamiento Supabase."""
    return SupabaseStorageRepository(client=client)


DocumentRepoDep = Annotated[DocumentRepository, Depends(get_document_repository)]
VectorRepoDep = Annotated[VectorRepository, Depends(get_vector_repository)]
ExtractorDep = Annotated[DocumentExtractor, Depends(get_extractor)]
StorageRepoDep = Annotated[DocumentStorageRepository, Depends(get_storage_repository)]


async def get_document_service(
    sql_repo: DocumentRepoDep, vector_repo: VectorRepoDep, extractor: ExtractorDep, storage_repo: StorageRepoDep
) -> DocumentService:
    """Fábrica que construye el DocumentService inyectándole la infraestructura real.

    FastAPI ejecutará esto automáticamente cada vez que un endpoint lo pida.
    """
    return DocumentService(
        sql_repo=sql_repo,
        vector_repo=vector_repo,
        extractor=extractor,
        storage_repo=storage_repo,
    )
