"""DocumentService: Orchestrates document creation and storage across repositories."""

import re

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
    def _sanitize_filename(filename: str) -> str:
        """Sanitizes filenames to a safe storage-friendly format."""
        base_name = filename.rsplit("/", maxsplit=1)[-1].rsplit("\\", maxsplit=1)[-1]
        normalized = re.sub(r"[^A-Za-z0-9._-]", "_", base_name).strip("._")
        if not normalized:
            return "document.pdf"
        if "." not in normalized:
            return f"{normalized}.pdf"
        return normalized

    @classmethod
    def build_storage_path(cls, document_id: int, filename: str | None = None) -> str:
        """Builds deterministic storage path for each document."""
        if not filename:
            return f"documents/{document_id}.pdf"
        safe_name = cls._sanitize_filename(filename)
        return f"documents/{document_id}/{safe_name}"

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
        document_id = save_doc.id
        storage_path = self.build_storage_path(document_id, filename)

        try:
            await self.storage_repo.upload_file(path=storage_path, file=file, content_type=content_type)
        except Exception as e:
            await self.sql_repo.delete(document_id)
            raise RuntimeError(f"Failed to store document file: {e!s}") from e

        save_doc.file_path = storage_path
        save_doc.file_name = filename
        updated_saved_doc = await self.sql_repo.update(save_doc)
        if not updated_saved_doc:
            raise RuntimeError("Failed to persist document file metadata")

        try:
            await self.vector_repo.add_vectors(index_name=index_name, document_id=document_id, chunks=parsed_document)
        except Exception as e:
            try:
                await self.storage_repo.delete_file(path=storage_path)
            except Exception:
                pass
            await self.sql_repo.delete(document_id)
            raise RuntimeError(f"Failed to store document vectors: {e!s}") from e

        return updated_saved_doc

    async def get_documents(self) -> list[DocumentTable]:
        """Retrieves all documents from the relational repository."""
        return await self.sql_repo.get_all()

    async def get_document(self, id: int) -> DocumentTable | None:
        """Retrieves a single document by ID from the relational repository."""
        return await self.sql_repo.get_by_id(id)

    async def delete_document(self, id: int, index_name: str = "contracts_index") -> bool:
        """Deletes a document from both the relational and vector repositories."""
        doc = await self.sql_repo.get_by_id(id)
        if not doc:
            raise ValueError(f"Document with id {id} not found")

        try:
            await self.vector_repo.delete_vectors(index_name=index_name, document_id=id)
        except Exception as e:
            raise RuntimeError(f"Failed to delete document vectors: {e!s}") from e

        try:
            storage_path = doc.file_path if doc.file_path else self.build_storage_path(id)
            await self.storage_repo.delete_file(path=storage_path)
        except Exception as e:
            raise RuntimeError(f"Failed to delete document file: {e!s}") from e

        return await self.sql_repo.delete(id)

    async def update_document(
        self,
        id: int,
        data: UpdateDocumentRequest,
        file: bytes | None = None,
        filename: str | None = None,
        content_type: str = "application/pdf",
        index_name: str = "contracts_index",
    ) -> DocumentTable:
        """Updates an existing document in the relational repository."""
        doc = await self.sql_repo.get_by_id(id)
        if not doc:
            raise ValueError(f"Document with id {id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(doc, field, value)

        if file is not None:
            if not filename:
                raise ValueError("Filename is required when replacing the file")

            parsed_document = await self.extractor.extract(file=file, filename=filename)
            if not parsed_document:
                raise ValueError("Failed to extract data from the replacement document.")

            old_storage_path = doc.file_path if doc.file_path else self.build_storage_path(id)
            new_storage_path = self.build_storage_path(id, filename)

            await self.storage_repo.upload_file(path=new_storage_path, file=file, content_type=content_type)

            try:
                await self.vector_repo.add_vectors(index_name=index_name, document_id=id, chunks=parsed_document)
            except Exception as e:
                if new_storage_path != old_storage_path:
                    try:
                        await self.storage_repo.delete_file(path=new_storage_path)
                    except Exception:
                        pass
                raise RuntimeError(f"Failed to update document vectors: {e!s}") from e

            if new_storage_path != old_storage_path:
                try:
                    await self.storage_repo.delete_file(path=old_storage_path)
                except Exception:
                    pass

            doc.file_path = new_storage_path
            doc.file_name = filename

        updated_doc = await self.sql_repo.update(doc)
        if not updated_doc:
            raise RuntimeError(f"Failed to update document with id {id}")
        return updated_doc

    async def get_document_signed_url(self, id: int, expires_in: int = 3600) -> str:
        """Returns a temporary signed URL for a stored document file."""
        doc = await self.sql_repo.get_by_id(id)
        if not doc:
            raise ValueError(f"Document with id {id} not found")

        storage_path = doc.file_path if doc.file_path else self.build_storage_path(id)
        return await self.storage_repo.create_signed_url(path=storage_path, expires_in=expires_in)
