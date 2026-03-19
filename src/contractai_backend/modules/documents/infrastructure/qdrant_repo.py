"""Repository implementation for managing document vectors in Qdrant, integrated with LlamaIndex for vector storage and retrieval."""

from fastapi.concurrency import run_in_threadpool
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http import models

from contractai_backend.modules.documents.application.repositories.base_vectorial import VectorRepository


class LlamaIndexQdrantRepository(VectorRepository):
    def __init__(self, async_client: AsyncQdrantClient, sync_client: QdrantClient):
        self.async_client = async_client
        self.sync_client = sync_client

    def _get_node_parser(self):
        """Configura el NodeParser de LlamaIndex para dividir el texto en ventanas de 3 oraciones."""
        return SentenceWindowNodeParser.from_defaults(
            window_size=3,
            window_metadata_key="window",
            original_text_metadata_key="original_text",
        )

    async def _ensure_collection(self, index: str):
        """Asegura que la colección de documentos exista en Qdrant."""
        exists = await self.async_client.collection_exists(collection_name=index)
        if not exists:
            await self.async_client.recreate_collection(
                collection_name=index,
                vectors_config=models.VectorParams(
                size=768,
                distance=models.Distance.COSINE
                )
            )
        try:
            await self.async_client.create_payload_index(
                collection_name=index,
                field_name="filename",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
        except (ValueError, RuntimeError) as e:
            if "already exists" not in str(e):
                raise

    async def delete_vectors(self, index_name: str, filename: str):
        """Elimina todos los vectores asociados a un documento específico en Qdrant, identificados por el nombre del archivo."""
        exists = await self.async_client.collection_exists(collection_name=index_name)
        if not exists:
            raise ValueError(f"Collection '{index_name}' does not exist in Qdrant.")

        await self.async_client.delete(
            collection_name=index_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[models.FieldCondition(key="filename", match=models.MatchValue(value=filename))]
                )
            )
        )

    async def add_vectors(self, index_name: str, filename: str, chunks: list) -> None:
        """Ejecuta la ingesta de LlamaIndex hacia Qdrant."""
        await self._ensure_collection(index_name)
        await self.delete_vectors(index_name, filename)

        vector_store = QdrantVectorStore(
            client=self.sync_client,
            collection_name=index_name
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        try:
            await run_in_threadpool(
                lambda: VectorStoreIndex.from_documents(
                    chunks,
                    storage_context=storage_context,
                    node_parser=self._get_node_parser(),
                    show_progress=True,
                )
            )
        except Exception as e:
            raise RuntimeError(f"Error al subir vectores a Qdrant: {e}") from e
        finally:
            self.sync_client.close()
