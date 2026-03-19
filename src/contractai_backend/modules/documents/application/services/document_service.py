"""DocumentService: Orchestrates document creation, data extraction, and storage in both relational and vector repositories."""

from ...api.schemas import CreateDocumentRequest
from ...domain.entities import DocumentTable
from ..repositories import DocumentExtractor, DocumentRepository, VectorRepository


class DocumentService:
    def __init__(
        self,
        sql_repo: DocumentRepository,
        vector_repo: VectorRepository,
        extractor: DocumentExtractor
    ):
        self.sql_repo = sql_repo
        self.vector_repo = vector_repo
        self.extractor = extractor

    async def create_document(
        self, file: bytes, filename: str, data: CreateDocumentRequest, index_name: str =  "contracts_index") -> DocumentTable:
        """Creates a new document, extracts data, and stores it in both repositories."""
        parsed_document = await self.extractor.extract(file=file, filename=filename)

        if not parsed_document:
            raise ValueError("Failed to extract data from the document.")

        new_document = DocumentTable(
            name=data.name,
            client=data.client,
            type=data.type,
            start_date=data.start_date,
            end_date=data.end_date,
            value=data.value,
            currency=data.currency,
            licenses=data.licenses,
        )

        save_doc = await self.sql_repo.save(new_document)

        try:
            await self.vector_repo.add_vectors(
                index_name=index_name,
                document_id=save_doc.id,
                chunks=parsed_document
            )
        except Exception as e:
            await self.sql_repo.delete(save_doc.id)
            raise RuntimeError(f"Failed to store document vectors: {e!s}") from e

        return save_doc

    async def get_documents(self) -> list[DocumentTable]:
        """Retrieves all documents from the relational repository."""
        return await self.sql_repo.get_all()

    async def get_document(self, id: int) -> DocumentTable | None:
        """Retrieves a single document by ID from the relational repository."""
        return await self.sql_repo.get_by_id(id)

    async def delete_document(self, id: int, index_name: str = "contracts_index") -> bool:
        """Deletes a document from both the relational and vector repositories."""
        try:
            await self.vector_repo.delete_vectors(index_name=index_name, document_id=id)
        except Exception as e:
            raise RuntimeError(f"Failed to delete document vectors: {e!s}") from e
        return await self.sql_repo.delete(id)
