"""Reposity of vectors for Qdrant, using LlamaIndex to manage the index and retrieval logic."""
from langchain_community.retrievers.llama_index import LlamaIndexRetriever
from langchain_core.documents.base import Document
from llama_index.core import VectorStoreIndex
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient

from ..application.repositories.base_vectorial import VectorRepository
from ..domain.exceptions import VectorDatabaseUnavailableError, VectorSearchError


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
            local_retriever = LlamaIndexRetriever(index=llama_retriever)
            docs: list[Document] = await local_retriever.ainvoke(query)
        except Exception as e:
            raise VectorSearchError(message=f"Fallo en el retriever de LlamaIndex: {e!s}") from e

        contextos_formateados = []
        for doc in docs:
            filename = doc.metadata.get("filename", "Desconocido")
            texto = doc.page_content
            contextos_formateados.append(f"[Fuente: {filename}]\n{texto}")

        return "\n\n---\n\n".join(contextos_formateados)
