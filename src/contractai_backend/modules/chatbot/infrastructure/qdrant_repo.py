"""Reposity of vectors for Qdrant, using LlamaIndex to manage the index and retrieval logic."""

from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient

from ..application.repositories.vector_repo import VectorRepository
from .agent.retriever import LlamaIndexWindowRetriever


class QdrantVectorRepository(VectorRepository):
    def __init__(self, collection_name: str, client: AsyncQdrantClient, index: VectorStoreIndex):

        self.client = client
        self.collection_name = collection_name
        self.index = index
        self.retriever = LlamaIndexWindowRetriever(index=self.index, top_k=5)

    @classmethod
    async def build(cls, client: AsyncQdrantClient, collection_name: str) -> "QdrantVectorRepository":
        """Factory method para construir el repositorio, asegurando la creación del índice y la colección en Qdrant."""
        vector_store = QdrantVectorStore(aclient=client, collection_name=collection_name)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        return cls(collection_name=collection_name, client=client, index=index)

    async def search_documents(self, query: str, limit: int = 5) -> str:
        """Busca documentos relevantes en Qdrant usando el retriever de LlamaIndex y devuelve un string formateado con los resultados."""
        self.retriever.top_k = limit
        docs = await self.retriever.ainvoke(query)

        if not docs:
            return "No se encontraron documentos relevantes para tu consulta."

        contextos_formateados = []
        for doc in docs:
            filename = doc.metadata.get("filename", "Desconocido")
            texto = doc.page_content
            contextos_formateados.append(f"[Fuente: {filename}]\n{texto}")

        return "\n\n---\n\n".join(contextos_formateados)
