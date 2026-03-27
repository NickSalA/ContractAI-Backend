"""Reposity of vectors for Qdrant, using LlamaIndex to manage the index and retrieval logic."""

from typing import Any

from llama_index.core import QueryBundle, VectorStoreIndex
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from llama_index.core.schema import NodeWithScore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient

from ..application.repositories import VectorRepository
from ..domain import VectorDatabaseUnavailableError, VectorSearchError


class QdrantVectorRepository(VectorRepository):
    def __init__(self, collection_name: str, client: AsyncQdrantClient, index: VectorStoreIndex):
        self.client: AsyncQdrantClient = client
        self.collection_name: str = collection_name
        self.index: VectorStoreIndex = index

    @classmethod
    async def build(cls, client: AsyncQdrantClient, collection_name: str) -> "QdrantVectorRepository":
        """Factory method para construir el repositorio, asegurando la creación del índice y la colección en Qdrant."""
        try:
            vector_store = QdrantVectorStore(aclient=client, collection_name=collection_name)
            index: VectorStoreIndex = VectorStoreIndex.from_vector_store(vector_store=vector_store)
            return cls(collection_name=collection_name, client=client, index=index)
        except Exception as e:
            raise VectorDatabaseUnavailableError(message=f"No se pudo conectar con Qdrant: {e!s}") from e

    async def search_documents(self, query: str, limit: int = 5) -> str:
        """Busca documentos relevantes en Qdrant usando el retriever de LlamaIndex y devuelve un string formateado."""
        try:
            llama_retriever: BaseRetriever = self.index.as_retriever(similarity_top_k=limit)
            nodes: list[NodeWithScore] = await llama_retriever.aretrieve(str_or_query_bundle=query)
            processor = MetadataReplacementPostProcessor(target_metadata_key="window")
            new_nodes: list[NodeWithScore] = processor.postprocess_nodes(nodes, query_bundle=QueryBundle(query))
        except Exception as e:
            raise VectorSearchError(message=f"Fallo en el retriever de LlamaIndex: {e!s}") from e

        contextos_formateados: list[str] = []
        for node in new_nodes:
            filename: Any = node.metadata.get("filename", "Desconocido")
            texto: str = node.text
            contextos_formateados.append(f"[Fuente: {filename}]\n{texto}")

        return "\n\n---\n\n".join(contextos_formateados)
