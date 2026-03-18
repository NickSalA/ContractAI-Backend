import os
import tempfile

from llama_parse import LlamaParse, ResultType

from contractai_backend.modules.documents.application.interfaces import IExtractor


class LlamaParseExtractor(IExtractor):
    def __init__(
        self,
        api_key: str
        ):
        self.parser = LlamaParse(
            api_key=api_key,
            result_type=ResultType.MD,
            verbose=False,
            language="es",
        )
    async def extract(self, file: bytes, filename: str) -> list:
        """Extracts structured data from a document using LlamaParse."""
        extension = os.path.splitext(filename)[1].lower()

        with tempfile.NamedTemporaryFile(delete=True, suffix=extension) as temp_file:
            temp_file.write(file)
            temp_file.flush()

            documents = await self.parser.aload_data(file_path=temp_file.name)

        for doc in documents:
            doc.metadata["filename"] = filename

        return documents
