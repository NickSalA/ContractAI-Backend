from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from qdrant_client import AsyncQdrantClient
from ....shared.config import settings
from ..application.repositories.vector_repo import VectorRepository


class QdrantVectorRepository(VectorRepository):
    def __init__(self, collection_name: str, client: AsyncQdrantClient):
        Settings.embed_model = OpenAIEmbedding(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_EMBEDDING_MODEL_NAME or "text-embedding-3-small"
        )

        self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        self.vector_store = QdrantVectorStore(client=self.client, collection_name=settings.INDEX_NAME)
        self.index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store)

    def search_documents(self, query: str, limit: int = 5) -> str:
        retriever = self.index.as_retriever(similarity_top_k=limit)
        nodes = retriever.retrieve(query)

        context = "\n\n---\n\n".join([n.get_content() for n in nodes])
        return context if context else "No se encontró información normativa sobre esta consulta."