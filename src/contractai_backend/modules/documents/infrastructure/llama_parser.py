"""LlamaParse-based document parser implementation."""

import tempfile
from pathlib import Path

from llama_parse import LlamaParse, ResultType

from ....shared.config import settings
from ..application.repositories import DocumentExtractor
from ..domain.exceptions import DocumentExtractionError


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
        extension: str = Path(filename).suffix.lower()
        temp_path = None

        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(file)
            temp_file.flush()
            temp_path: str = temp_file.name
        try:
            documents = await self.parser.aload_data(file_path=temp_path)

            for doc in documents:
                doc.metadata["filename"] = filename
            return documents

        except Exception as e:
            raise DocumentExtractionError(f"El servicio fallo al procesar '{filename}': {e!s}") from e
        finally:
            if temp_path and Path(temp_path).exists():
                Path(temp_path).unlink()
