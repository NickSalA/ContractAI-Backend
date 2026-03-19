"""DocumentService: Orchestrates document creation and storage across repositories."""

from ...api.schemas import CreateDocumentRequest, UpdateDocumentRequest
from ...domain.entities import DocumentTable
from ..repositories import DocumentExtractor, DocumentRepository, DocumentStorageRepository, VectorRepository


class DocumentService:
    def __init__(
        self,
        sql_repo: DocumentRepository,
        vector_repo: VectorRepository,
        extractor: DocumentExtractor,
        storage_repo: DocumentStorageRepository,
    ):
        self.sql_repo = sql_repo
        self.vector_repo = vector_repo
        self.extractor = extractor
        self.storage_repo = storage_repo

    @staticmethod
    def build_storage_path(document_id: int) -> str:
        """Builds deterministic storage path for each document."""
        return f"documents/{document_id}.pdf"

    async def create_document(
        self,
        file: bytes,
        filename: str,
        data: CreateDocumentRequest,
        content_type: str = "application/pdf",
        index_name: str = "contracts_index",
    ) -> DocumentTable:
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
        storage_path = self.build_storage_path(save_doc.id)

        try:
            await self.storage_repo.upload_file(path=storage_path, file=file, content_type=content_type)
        except Exception as e:
            await self.sql_repo.delete(save_doc.id)
            raise RuntimeError(f"Failed to store document file: {e!s}") from e

        try:
            await self.vector_repo.add_vectors(index_name=index_name, document_id=save_doc.id, chunks=parsed_document)
        except Exception as e:
            try:
                await self.storage_repo.delete_file(path=storage_path)
            except Exception:
                pass
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

        try:
            await self.storage_repo.delete_file(path=self.build_storage_path(id))
        except Exception as e:
            raise RuntimeError(f"Failed to delete document file: {e!s}") from e

        return await self.sql_repo.delete(id)

    async def update_document(self, id: int, data: UpdateDocumentRequest) -> DocumentTable:
        """Updates an existing document in the relational repository."""
        doc = await self.sql_repo.get_by_id(id)
        if not doc:
            raise ValueError(f"Document with id {id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(doc, field, value)

        updated_doc = await self.sql_repo.update(doc)
        if not updated_doc:
            raise RuntimeError(f"Failed to update document with id {id}")
        return updated_doc

    async def get_document_signed_url(self, id: int, expires_in: int = 3600) -> str:
        """Returns a temporary signed URL for a stored document file."""
        doc = await self.sql_repo.get_by_id(id)
        if not doc:
            raise ValueError(f"Document with id {id} not found")

        storage_path = self.build_storage_path(id)
        return await self.storage_repo.create_signed_url(path=storage_path, expires_in=expires_in)
