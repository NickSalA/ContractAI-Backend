"""Repository implementation for managing document vectors in Qdrant, integrated with LlamaIndex for vector storage and retrieval."""

from fastapi.concurrency import run_in_threadpool
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http import models

from contractai_backend.modules.documents.application.interfaces.vector_repo import IVectorRepository


class LlamaIndexQdrantRepository(IVectorRepository):
    def __init__(self, async_client: AsyncQdrantClient, sync_client: QdrantClient):
        self.async_client = async_client
        self.sync_client = sync_client # LlamaIndex a veces requiere el cliente síncrono para su VectorStore

    def get_node_parser(self):
        """Configura el NodeParser de LlamaIndex para dividir el texto en ventanas de 3 oraciones."""
        return SentenceWindowNodeParser.from_defaults(
            window_size=3,
            window_metadata_key="window",
            original_text_metadata_key="original_text",
        )

    async def _ensure_collection(self, index: str):
        exists = await self.async_client.collection_exists(collection_name=index)
        if not exists:
            await self.async_client.recreate_collection(
                collection_name=index,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
            )
        # ... (resto de tu lógica de ensure_collection)

    async def delete_document_vectors(self, index_name: str, filename: str):
        """Elimina todos los vectores asociados a un documento específico en Qdrant, identificados por el nombre del archivo."""
        exists = await self.async_client.collection_exists(collection_name=index_name)
        if not exists:
            return # Si no existe, no hay nada que borrar

        await self.async_client.delete(
            collection_name=index_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[models.FieldCondition(key="filename", match=models.MatchValue(value=filename))]
                )
            )
        )

    async def upload_document_chunks(self, index_name: str, filename: str, chunks: list) -> None:
        """Ejecuta la ingesta de LlamaIndex hacia Qdrant."""
        await self._ensure_collection(index_name)
        await self.delete_document_vectors(index_name, filename)

        # Configuramos el VectorStore de LlamaIndex apuntando a Qdrant
        vector_store = QdrantVectorStore(
            client=self.sync_client,
            collection_name=index_name
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        try:
            # LlamaIndex detectará Settings.embed_model automáticamente aquí
            await run_in_threadpool(
                lambda: VectorStoreIndex.from_documents(
                    chunks,
                    storage_context=storage_context,
                    node_parser=self.get_node_parser(),
                    show_progress=True,
                )
            )
        except Exception as e:
            raise RuntimeError(f"Error al subir vectores a Qdrant: {e}") from e
