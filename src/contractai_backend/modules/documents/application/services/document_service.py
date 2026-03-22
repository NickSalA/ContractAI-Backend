"""DocumentService: Orchestrates document creation and storage across repositories."""

from collections.abc import Sequence

from loguru import logger

from ...api.schemas import CreateDocumentRequest, FileRequest, UpdateDocumentRequest
from ...domain.entities import DocumentTable
from ...domain.exceptions import (
    DocumentExtractionError,
    DocumentFileMissingError,
    DocumentNotFoundError,
    DocumentTransactionError,
    InvalidDocumentFileError,
)
from ..repositories import DocumentExtractor, DocumentRepository, DocumentStorageRepository, VectorRepository


class DocumentService:
    def __init__(
        self,
        sql_repo: DocumentRepository,
        vector_repo: VectorRepository,
        extractor: DocumentExtractor,
        storage_repo: DocumentStorageRepository,
    ):
        self.sql_repo: DocumentRepository = sql_repo
        self.vector_repo: VectorRepository = vector_repo
        self.extractor: DocumentExtractor = extractor
        self.storage_repo: DocumentStorageRepository = storage_repo

    async def create_document(
        self,
        data: CreateDocumentRequest,
        file_data: FileRequest,
        index_name: str = "contracts_index",
    ) -> DocumentTable:
        """Creates a new document, orchestrating SQL, Storage, and Vector DB."""
        parsed_document = await self.extractor.extract(file=file_data.content, filename=file_data.filename)
        if not parsed_document:
            raise DocumentExtractionError()

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
        save_doc: DocumentTable = await self.sql_repo.save(entity=new_document)
        document_id: int = save_doc.id

        storage_path = None
        vectors_added = False

        try:
            storage_path: str = await self.storage_repo.upload_file(
                document_id=document_id, file=file_data.content, filename=file_data.filename, content_type=file_data.content_type
            )

            await self.vector_repo.add_vectors(index_name=index_name, document_id=document_id, chunks=parsed_document)
            vectors_added = True

            save_doc.file_path: str = storage_path
            save_doc.file_name: str = file_data.filename
            updated_saved_doc: DocumentTable | None = await self.sql_repo.update(entity=save_doc)

            if not updated_saved_doc:
                raise DocumentTransactionError(operation="create", details=f"Failed to update document with id {document_id} in SQL after creation")

            return updated_saved_doc

        except Exception as e:
            if vectors_added:
                try:
                    await self.vector_repo.delete_vectors(index_name=index_name, document_id=document_id)
                except Exception:
                    pass

            if storage_path:
                try:
                    await self.storage_repo.delete_file(path=storage_path)
                except Exception:
                    pass

            try:
                await self.sql_repo.delete(id=document_id)
            except Exception:
                pass
            raise DocumentTransactionError(operation="create", details=str(object=e)) from e

    async def get_documents(self) -> Sequence[DocumentTable]:
        """Retrieves all documents from the relational repository."""
        return await self.sql_repo.get_all()

    async def get_document(self, id: int) -> DocumentTable | None:
        """Retrieves a single document by ID from the relational repository."""
        return await self.sql_repo.get_by_id(id)

    async def delete_document(self, id: int, index_name: str = "contracts_index") -> bool:
        """Deletes a document orchestrating SQL, VectorDB, and Storage."""
        doc: DocumentTable | None = await self.sql_repo.get_by_id(id)
        if not doc:
            raise DocumentNotFoundError(document_id=id)

        try:
            await self.vector_repo.delete_vectors(index_name=index_name, document_id=id)
        except Exception as e:
            raise DocumentTransactionError(operation="delete vectors", details=str(object=e)) from e

        if doc.file_path:
            try:
                await self.storage_repo.delete_file(path=doc.file_path)
            except Exception as e:
                logger.exception(f"Failed to delete document file from storage: {e!s}")

        return await self.sql_repo.delete(id)

    async def update_document(
        self,
        id: int,
        data: UpdateDocumentRequest,
        file_data: FileRequest | None = None,
        index_name: str = "contracts_index",
    ) -> DocumentTable:
        """Updates an existing document orchestrating SQL, VectorDB, and Storage."""
        doc: DocumentTable | None = await self.sql_repo.get_by_id(id)
        if not doc:
            raise DocumentNotFoundError(document_id=id)

        old_storage_path: str | None = doc.file_path

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(doc, field, value)

        if file_data is None:
            updated_doc: DocumentTable | None = await self.sql_repo.update(entity=doc)
            if not updated_doc:
                raise DocumentTransactionError(operation="update", details=f"Failed to update document with id {id} in SQL without file changes")
            return updated_doc

        if not file_data.filename or file_data.content_type is None:
            raise InvalidDocumentFileError()

        parsed_document = await self.extractor.extract(file=file_data.content, filename=file_data.filename)
        if not parsed_document:
            raise DocumentExtractionError()

        new_storage_path = None

        try:
            new_storage_path: str = await self.storage_repo.upload_file(
                document_id=id, file=file_data.content, filename=file_data.filename, content_type=file_data.content_type
            )

            await self.vector_repo.add_vectors(index_name=index_name, document_id=id, chunks=parsed_document)

            doc.file_path: str = new_storage_path
            doc.file_name: str = file_data.filename
            updated_doc: DocumentTable | None = await self.sql_repo.update(entity=doc)

            if not updated_doc:
                raise DocumentTransactionError(operation="update", details=f"Failed to update document with id {id} in SQL")

            if old_storage_path and old_storage_path != new_storage_path:
                try:
                    await self.storage_repo.delete_file(path=old_storage_path)
                except Exception:
                    pass

            return updated_doc

        except Exception as e:
            if new_storage_path:
                try:
                    await self.storage_repo.delete_file(path=new_storage_path)
                except Exception:
                    pass

            raise DocumentTransactionError(operation="update", details=str(object=e)) from e

    async def get_document_signed_url(self, id: int, expires_in: int = 3600) -> str:
        """Returns a temporary signed URL for a stored document file."""
        doc: DocumentTable | None = await self.sql_repo.get_by_id(id)
        if not doc:
            raise DocumentNotFoundError(document_id=id)
        if doc.file_path is None:
            raise DocumentFileMissingError(document_id=id)

        storage_path: str = doc.file_path
        return await self.storage_repo.create_signed_url(path=storage_path, expires_in=expires_in)
