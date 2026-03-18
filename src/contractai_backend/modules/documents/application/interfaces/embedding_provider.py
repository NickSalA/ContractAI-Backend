
class IEmbeddingProvider:
    """Interface for embedding providers."""

    def embed(self, text: str) -> List[float]:
        """Generates an embedding vector for the given text."""
        raise NotImplementedError("Embedding provider must implement the embed method.")