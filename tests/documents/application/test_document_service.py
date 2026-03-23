"""Tests unitarios para DocumentService con mocks de repositorios."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from contractai_backend.modules.documents.api.schemas import CreateDocumentRequest, FileRequest, UpdateDocumentRequest
from contractai_backend.modules.documents.application.services.document_service import DocumentService
from contractai_backend.modules.documents.domain.entities import DocumentTable
from contractai_backend.modules.documents.domain.exceptions import (
    DocumentExtractionError,
    DocumentFileMissingError,
    DocumentNotFoundError,
    DocumentTransactionError,
)
from contractai_backend.modules.documents.domain.value_objs import DocumentState, DocumentType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(id: int = 1, file_path: str | None = "docs/1/file.pdf") -> DocumentTable:
    return DocumentTable(
        id=id,
        name="Contrato Test",
        client="Cliente Test",
        type=DocumentType.LICENSES,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        value=1000.0,
        currency="PEN",
        licenses=5,
        state=DocumentState.ACTIVE,
        file_path=file_path,
        file_name="file.pdf",
    )


def _make_service(
    sql_repo=None,
    vector_repo=None,
    extractor=None,
    storage_repo=None,
) -> DocumentService:
    return DocumentService(
        sql_repo=sql_repo or AsyncMock(),
        vector_repo=vector_repo or AsyncMock(),
        extractor=extractor or AsyncMock(),
        storage_repo=storage_repo or AsyncMock(),
    )


def _create_request() -> CreateDocumentRequest:
    return CreateDocumentRequest(
        name="Contrato Test",
        client="Cliente Test",
        type=DocumentType.LICENSES,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        value=1000.0,
        currency="PEN",
        licenses=5,
    )


def _file_request() -> FileRequest:
    return FileRequest(content=b"pdf content", filename="file.pdf", content_type="application/pdf")


# ---------------------------------------------------------------------------
# create_document
# ---------------------------------------------------------------------------

class TestCreateDocument:
    @pytest.mark.asyncio
    async def test_create_document_success(self):
        saved = _make_doc()
        updated = _make_doc(file_path="docs/1/file.pdf")

        sql_repo = AsyncMock()
        sql_repo.save.return_value = saved
        sql_repo.update.return_value = updated

        vector_repo = AsyncMock()
        extractor = AsyncMock()
        extractor.extract.return_value = ["chunk1", "chunk2"]

        storage_repo = AsyncMock()
        storage_repo.upload_file.return_value = "docs/1/file.pdf"

        service = _make_service(sql_repo, vector_repo, extractor, storage_repo)
        result = await service.create_document(_create_request(), _file_request())

        assert result == updated
        sql_repo.save.assert_called_once()
        storage_repo.upload_file.assert_called_once()
        vector_repo.add_vectors.assert_called_once()
        sql_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_extraction_fails_raises(self):
        extractor = AsyncMock()
        extractor.extract.return_value = []  # vacío → falla

        service = _make_service(extractor=extractor)
        with pytest.raises(DocumentExtractionError):
            await service.create_document(_create_request(), _file_request())

    @pytest.mark.asyncio
    async def test_create_document_storage_fails_rollbacks_sql(self):
        saved = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.save.return_value = saved

        extractor = AsyncMock()
        extractor.extract.return_value = ["chunk"]

        storage_repo = AsyncMock()
        storage_repo.upload_file.side_effect = Exception("storage down")

        service = _make_service(sql_repo=sql_repo, extractor=extractor, storage_repo=storage_repo)

        with pytest.raises(DocumentTransactionError):
            await service.create_document(_create_request(), _file_request())

        sql_repo.delete.assert_called_once_with(id=saved.id)

    @pytest.mark.asyncio
    async def test_create_document_vector_fails_rollbacks_storage_and_sql(self):
        saved = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.save.return_value = saved

        extractor = AsyncMock()
        extractor.extract.return_value = ["chunk"]

        storage_repo = AsyncMock()
        storage_repo.upload_file.return_value = "docs/1/file.pdf"

        vector_repo = AsyncMock()
        vector_repo.add_vectors.side_effect = Exception("qdrant down")

        service = _make_service(sql_repo=sql_repo, vector_repo=vector_repo, extractor=extractor, storage_repo=storage_repo)

        with pytest.raises(DocumentTransactionError):
            await service.create_document(_create_request(), _file_request())

        storage_repo.delete_file.assert_called_once()
        sql_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_sql_update_returns_none_raises(self):
        saved = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.save.return_value = saved
        sql_repo.update.return_value = None  # falla silenciosa

        extractor = AsyncMock()
        extractor.extract.return_value = ["chunk"]
        storage_repo = AsyncMock()
        storage_repo.upload_file.return_value = "docs/1/file.pdf"
        vector_repo = AsyncMock()

        service = _make_service(sql_repo=sql_repo, vector_repo=vector_repo, extractor=extractor, storage_repo=storage_repo)

        with pytest.raises(DocumentTransactionError):
            await service.create_document(_create_request(), _file_request())


# ---------------------------------------------------------------------------
# get_documents / get_document
# ---------------------------------------------------------------------------

class TestGetDocuments:
    @pytest.mark.asyncio
    async def test_get_documents_returns_all(self):
        docs = [_make_doc(1), _make_doc(2)]
        sql_repo = AsyncMock()
        sql_repo.get_all.return_value = docs

        service = _make_service(sql_repo=sql_repo)
        result = await service.get_documents()

        assert result == docs
        sql_repo.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_returns_doc(self):
        doc = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc

        service = _make_service(sql_repo=sql_repo)
        result = await service.get_document(1)

        assert result == doc

    @pytest.mark.asyncio
    async def test_get_document_not_found_returns_none(self):
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = None

        service = _make_service(sql_repo=sql_repo)
        result = await service.get_document(99)

        assert result is None


# ---------------------------------------------------------------------------
# delete_document
# ---------------------------------------------------------------------------

class TestDeleteDocument:
    @pytest.mark.asyncio
    async def test_delete_document_success(self):
        doc = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc
        sql_repo.delete.return_value = True
        vector_repo = AsyncMock()
        storage_repo = AsyncMock()

        service = _make_service(sql_repo=sql_repo, vector_repo=vector_repo, storage_repo=storage_repo)
        result = await service.delete_document(1)

        assert result is True
        vector_repo.delete_vectors.assert_called_once()
        storage_repo.delete_file.assert_called_once_with(path=doc.file_path)

    @pytest.mark.asyncio
    async def test_delete_document_not_found_raises(self):
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = None

        service = _make_service(sql_repo=sql_repo)
        with pytest.raises(DocumentNotFoundError):
            await service.delete_document(99)

    @pytest.mark.asyncio
    async def test_delete_document_without_file_skips_storage(self):
        doc = _make_doc(file_path=None)
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc
        sql_repo.delete.return_value = True
        vector_repo = AsyncMock()
        storage_repo = AsyncMock()

        service = _make_service(sql_repo=sql_repo, vector_repo=vector_repo, storage_repo=storage_repo)
        await service.delete_document(1)

        storage_repo.delete_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_document_vector_fails_raises_transaction_error(self):
        doc = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc
        vector_repo = AsyncMock()
        vector_repo.delete_vectors.side_effect = Exception("qdrant error")

        service = _make_service(sql_repo=sql_repo, vector_repo=vector_repo)
        with pytest.raises(DocumentTransactionError):
            await service.delete_document(1)


# ---------------------------------------------------------------------------
# update_document
# ---------------------------------------------------------------------------

class TestUpdateDocument:
    @pytest.mark.asyncio
    async def test_update_document_without_file(self):
        doc = _make_doc()
        updated = _make_doc()
        updated.name = "Nuevo Nombre"

        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc
        sql_repo.update.return_value = updated

        service = _make_service(sql_repo=sql_repo)
        result = await service.update_document(1, UpdateDocumentRequest(name="Nuevo Nombre"))

        assert result.name == "Nuevo Nombre"
        sql_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_not_found_raises(self):
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = None

        service = _make_service(sql_repo=sql_repo)
        with pytest.raises(DocumentNotFoundError):
            await service.update_document(99, UpdateDocumentRequest(name="X"))

    @pytest.mark.asyncio
    async def test_update_document_with_file_success(self):
        doc = _make_doc()
        updated = _make_doc(file_path="docs/1/new.pdf")

        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc
        sql_repo.update.return_value = updated

        extractor = AsyncMock()
        extractor.extract.return_value = ["chunk"]
        storage_repo = AsyncMock()
        storage_repo.upload_file.return_value = "docs/1/new.pdf"
        vector_repo = AsyncMock()

        service = _make_service(sql_repo=sql_repo, vector_repo=vector_repo, extractor=extractor, storage_repo=storage_repo)
        file_data = FileRequest(content=b"new pdf", filename="new.pdf", content_type="application/pdf")
        result = await service.update_document(1, UpdateDocumentRequest(), file_data=file_data)

        assert result.file_path == "docs/1/new.pdf"
        storage_repo.delete_file.assert_called_once_with(path="docs/1/file.pdf")  # old path deleted

    @pytest.mark.asyncio
    async def test_update_document_sql_update_returns_none_raises(self):
        doc = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc
        sql_repo.update.return_value = None

        service = _make_service(sql_repo=sql_repo)
        with pytest.raises(DocumentTransactionError):
            await service.update_document(1, UpdateDocumentRequest(name="X"))


# ---------------------------------------------------------------------------
# get_document_signed_url
# ---------------------------------------------------------------------------

class TestGetDocumentSignedUrl:
    @pytest.mark.asyncio
    async def test_returns_signed_url(self):
        doc = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc
        storage_repo = AsyncMock()
        storage_repo.create_signed_url.return_value = "https://storage/signed"

        service = _make_service(sql_repo=sql_repo, storage_repo=storage_repo)
        url = await service.get_document_signed_url(1)

        assert url == "https://storage/signed"

    @pytest.mark.asyncio
    async def test_document_not_found_raises(self):
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = None

        service = _make_service(sql_repo=sql_repo)
        with pytest.raises(DocumentNotFoundError):
            await service.get_document_signed_url(99)

    @pytest.mark.asyncio
    async def test_document_without_file_raises(self):
        doc = _make_doc(file_path=None)
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc

        service = _make_service(sql_repo=sql_repo)
        with pytest.raises(DocumentFileMissingError):
            await service.get_document_signed_url(1)
