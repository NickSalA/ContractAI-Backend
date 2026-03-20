"""DocumentService: Orchestrates document creation and storage across repositories."""

from loguru import logger

from ...api.schemas import CreateDocumentRequest, FileRequest, UpdateDocumentRequest
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

    async def create_document(
        self,
        data: CreateDocumentRequest,
        file_data: FileRequest,
        index_name: str = "contracts_index",
    ) -> DocumentTable:
        """Creates a new document, orchestrating SQL, Storage, and Vector DB."""
        parsed_document = await self.extractor.extract(file=file_data.content, filename=file_data.filename)
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
        document_id = save_doc.id

        storage_path = None
        vectors_added = False

        try:
            storage_path = await self.storage_repo.upload_file(
                document_id=document_id, file=file_data.content, filename=file_data.filename, content_type=file_data.content_type
            )

            await self.vector_repo.add_vectors(
                index_name=index_name, document_id=document_id, chunks=parsed_document
            )
            vectors_added = True

            save_doc.file_path = storage_path
            save_doc.file_name = file_data.filename
            updated_saved_doc = await self.sql_repo.update(save_doc)

            if not updated_saved_doc:
                raise RuntimeError("Failed to persist document file metadata in SQL")

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
                await self.sql_repo.delete(document_id)
            except Exception:
                pass
            raise RuntimeError(f"Document creation transaction failed and was rolled back: {e!s}") from e

    async def get_documents(self) -> list[DocumentTable]:
        """Retrieves all documents from the relational repository."""
        return await self.sql_repo.get_all()

    async def get_document(self, id: int) -> DocumentTable | None:
        """Retrieves a single document by ID from the relational repository."""
        return await self.sql_repo.get_by_id(id)

    async def delete_document(self, id: int, index_name: str = "contracts_index") -> bool:
        """Deletes a document orchestrating SQL, VectorDB, and Storage."""
        doc = await self.sql_repo.get_by_id(id)
        if not doc:
            raise ValueError(f"Document with id {id} not found")

        try:
            await self.vector_repo.delete_vectors(index_name=index_name, document_id=id)
        except Exception as e:
            raise RuntimeError(f"Failed to delete document vectors: {e!s}") from e

        if doc.file_path:
            try:
                await self.storage_repo.delete_file(doc.file_path)
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
        doc = await self.sql_repo.get_by_id(id)
        if not doc:
            raise ValueError(f"Document with id {id} not found")

        old_storage_path = doc.file_path

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(doc, field, value)

        if file_data is None:
            updated_doc = await self.sql_repo.update(doc)
            if not updated_doc:
                raise RuntimeError(f"Failed to update document metadata with id {id}")
            return updated_doc

        if not file_data.filename or file_data.content_type is None:
            raise ValueError("Filename and content type are required when replacing the file")

        parsed_document = await self.extractor.extract(file=file_data.content, filename=file_data.filename)
        if not parsed_document:
            raise ValueError("Failed to extract data from the replacement document.")

        new_storage_path = None

        try:
            new_storage_path = await self.storage_repo.upload_file(
                document_id=id,
                file=file_data.content,
                filename=file_data.filename,
                content_type=file_data.content_type
            )

            await self.vector_repo.add_vectors(
                index_name=index_name,
                document_id=id,
                chunks=parsed_document
            )

            doc.file_path = new_storage_path
            doc.file_name = file_data.filename
            updated_doc = await self.sql_repo.update(doc)

            if not updated_doc:
                raise RuntimeError(f"Failed to update document with id {id} in SQL")

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

            raise RuntimeError(f"Document update transaction failed: {e!s}") from e

    async def get_document_signed_url(self, id: int, expires_in: int = 3600) -> str:
        """Returns a temporary signed URL for a stored document file."""
        doc = await self.sql_repo.get_by_id(id)
        if not doc:
            raise ValueError(f"Document with id {id} not found")
        if doc.file_path is None:
            raise ValueError(f"Document with id {id} does not have an associated file")

        storage_path = doc.file_path
        return await self.storage_repo.create_signed_url(path=storage_path, expires_in=expires_in)
