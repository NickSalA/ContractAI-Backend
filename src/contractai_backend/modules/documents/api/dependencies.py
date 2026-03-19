"""Dependency Injection para el módulo de documentos."""

from typing import Annotated

from fastapi import Depends
from qdrant_client import AsyncQdrantClient, QdrantClient
from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.modules.documents.application.services.document_service import DocumentService
from contractai_backend.modules.documents.infrastructure import LlamaIndexQdrantRepository, LlamaParseExtractor, SQLModelDocumentRepository
from contractai_backend.shared.database import get_aclient, get_client, get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AsyncQdrantDep = Annotated[AsyncQdrantClient, Depends(get_aclient)]
SyncQdrantDep = Annotated[QdrantClient, Depends(get_client)]

async def get_document_service(
    session: SessionDep,
    async_qdrant: AsyncQdrantDep,
    sync_qdrant: SyncQdrantDep
) -> DocumentService:
    """Fábrica que construye el DocumentService inyectándole la infraestructura real.

    FastAPI ejecutará esto automáticamente cada vez que un endpoint lo pida.
    """
    extractor = LlamaParseExtractor()
    sql_repo = SQLModelDocumentRepository(session=session)
    vector_repo = LlamaIndexQdrantRepository(async_client=async_qdrant, sync_client=sync_qdrant)

    # B. Se las inyectamos al servicio a través de su constructor (El "Qué")
    return DocumentService(
        sql_repo=sql_repo,
        vector_repo=vector_repo,
        extractor=extractor
    )
