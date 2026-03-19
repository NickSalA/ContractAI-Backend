""""LlamaParse-based document parser implementation."""

import os
import tempfile

from llama_parse import LlamaParse, ResultType

from contractai_backend.modules.documents.application.repositories.base_extractor import DocumentExtractor
from contractai_backend.shared.config import settings


class LlamaParseExtractor(DocumentExtractor):
    def __init__(
        self,
        ):
        self.parser = LlamaParse(
            api_key=settings.LLAMA_PARSE_API_KEY,
            result_type=ResultType.MD,
            verbose=False,
            language="es",
        )
    async def extract(self, file: bytes, filename: str) -> list:
        """Extracts structured data from a document using LlamaParse."""
        extension = os.path.splitext(filename)[1].lower()

        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(file)
            temp_file.flush()
            temp_path = temp_file.name
        try:
            documents = await self.parser.aload_data(file_path=temp_path)
        finally:
            # Eliminar manualmente después de usarlo
            os.unlink(temp_path)

        for doc in documents:
            doc.metadata["filename"] = filename

        return documents
