"""Tests unitarios para DocumentService con mocks de repositorios."""

from datetime import date
from unittest.mock import AsyncMock

import pytest

from contractai_backend.modules.documents.api.schemas import CreateDocumentRequest, DocumentServiceItemRequest, FileRequest, UpdateDocumentRequest
from contractai_backend.modules.documents.application.services.document_service import DocumentService
from contractai_backend.modules.documents.domain.entities import DocumentTable, ServiceTable
from contractai_backend.modules.documents.domain.exceptions import (
    DocumentExtractionError,
    DocumentFileMissingError,
    DocumentNotFoundError,
    DocumentTransactionError,
    DocumentValidationError,
)
from contractai_backend.modules.documents.domain.value_objs import CurrencyType, DocumentState, DocumentType


def _make_doc(id: int = 1, file_path: str | None = "docs/1/file.pdf", organization_id: int = 1) -> DocumentTable:
    return DocumentTable(
        id=id,
        organization_id=organization_id,
        name="Contrato Test",
        client="Cliente Test",
        type=DocumentType.LICENSES,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        form_data={"value": 500.0, "currency": "USD", "owner": "IT"},
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


def _create_request(service_items: list[DocumentServiceItemRequest] | None = None) -> CreateDocumentRequest:
    return CreateDocumentRequest(
        name="Contrato Test",
        client="Cliente Test",
        type=DocumentType.LICENSES,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        form_data={"value": 0.0, "currency": "USD", "owner": "IT"},
        service_items=service_items or [],
    )


def _file_request() -> FileRequest:
    return FileRequest(content=b"pdf content", filename="file.pdf", content_type="application/pdf")


class TestCreateDocument:
    @pytest.mark.asyncio
    async def test_create_document_success(self):
        saved = _make_doc()
        updated = _make_doc(file_path="docs/1/file.pdf")

        sql_repo = AsyncMock()
        sql_repo.save.return_value = saved
        sql_repo.update.return_value = updated
        sql_repo.replace_document_services.return_value = []

        vector_repo = AsyncMock()
        extractor = AsyncMock()
        extractor.extract.return_value = ["chunk1", "chunk2"]

        storage_repo = AsyncMock()
        storage_repo.upload_file.return_value = "docs/1/file.pdf"

        service = _make_service(sql_repo, vector_repo, extractor, storage_repo)
        result = await service.create_document(_create_request(), _file_request(), organization_id=1)

        assert result == updated
        sql_repo.save.assert_called_once()
        sql_repo.replace_document_services.assert_called_once()
        storage_repo.upload_file.assert_called_once()
        vector_repo.add_vectors.assert_called_once()
        sql_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_with_invalid_service_ids_raises(self):
        sql_repo = AsyncMock()
        sql_repo.get_services_by_ids.return_value = []

        service = _make_service(sql_repo=sql_repo)
        request = _create_request(
            service_items=[
                DocumentServiceItemRequest(
                    service_id=10,
                    value=100.0,
                    currency=CurrencyType.PEN,
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 2, 1),
                )
            ]
        )

        with pytest.raises(DocumentValidationError, match="no existen"):
            await service.create_document(request, _file_request(), organization_id=1)

    @pytest.mark.asyncio
    async def test_create_document_extraction_fails_raises(self):
        extractor = AsyncMock()
        extractor.extract.return_value = []

        service = _make_service(extractor=extractor)
        with pytest.raises(DocumentExtractionError):
            await service.create_document(_create_request(), _file_request(), organization_id=1)

    @pytest.mark.asyncio
    async def test_create_document_storage_fails_rollbacks_sql(self):
        saved = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.save.return_value = saved
        sql_repo.replace_document_services.return_value = []

        extractor = AsyncMock()
        extractor.extract.return_value = ["chunk"]

        storage_repo = AsyncMock()
        storage_repo.upload_file.side_effect = Exception("storage down")

        service = _make_service(sql_repo=sql_repo, extractor=extractor, storage_repo=storage_repo)

        with pytest.raises(DocumentTransactionError):
            await service.create_document(_create_request(), _file_request(), organization_id=1)

        sql_repo.delete.assert_called_once_with(id=saved.id)

    @pytest.mark.asyncio
    async def test_create_document_vector_fails_rollbacks_storage_and_sql(self):
        saved = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.save.return_value = saved
        sql_repo.replace_document_services.return_value = []

        extractor = AsyncMock()
        extractor.extract.return_value = ["chunk"]

        storage_repo = AsyncMock()
        storage_repo.upload_file.return_value = "docs/1/file.pdf"

        vector_repo = AsyncMock()
        vector_repo.add_vectors.side_effect = Exception("qdrant down")

        service = _make_service(sql_repo=sql_repo, vector_repo=vector_repo, extractor=extractor, storage_repo=storage_repo)

        with pytest.raises(DocumentTransactionError):
            await service.create_document(_create_request(), _file_request(), organization_id=1)

        storage_repo.delete_file.assert_called_once()
        sql_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_recalculates_form_data_from_service_items(self):
        saved = _make_doc()
        updated = _make_doc(file_path="docs/1/file.pdf")

        sql_repo = AsyncMock()
        sql_repo.save.return_value = saved
        sql_repo.update.return_value = updated
        sql_repo.replace_document_services.return_value = []
        sql_repo.get_services_by_ids.return_value = [ServiceTable(id=2, organization_id=1, name="Hosting")]

        extractor = AsyncMock()
        extractor.extract.return_value = ["chunk1"]
        storage_repo = AsyncMock()
        storage_repo.upload_file.return_value = "docs/1/file.pdf"

        service = _make_service(sql_repo=sql_repo, extractor=extractor, storage_repo=storage_repo)
        request = _create_request(
            service_items=[
                DocumentServiceItemRequest(
                    service_id=2,
                    value=250.0,
                    currency=CurrencyType.USD,
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 4, 1),
                )
            ]
        )

        await service.create_document(request, _file_request(), organization_id=1)

        saved_entity = sql_repo.save.await_args.kwargs["entity"]
        assert saved_entity.form_data["value"] == 250.0
        assert saved_entity.form_data["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_create_document_with_service_dates_outside_contract_raises(self):
        sql_repo = AsyncMock()
        sql_repo.get_services_by_ids.return_value = [ServiceTable(id=2, organization_id=1, name="Hosting")]

        service = _make_service(sql_repo=sql_repo)
        request = _create_request(
            service_items=[
                DocumentServiceItemRequest(
                    service_id=2,
                    value=100.0,
                    currency=CurrencyType.USD,
                    start_date=date(2023, 12, 1),
                    end_date=date(2024, 2, 1),
                )
            ]
        )

        with pytest.raises(DocumentValidationError, match="dentro del rango del contrato"):
            await service.create_document(request, _file_request(), organization_id=1)

    @pytest.mark.asyncio
    async def test_create_document_with_mixed_currencies_raises(self):
        sql_repo = AsyncMock()
        sql_repo.get_services_by_ids.return_value = [
            ServiceTable(id=2, organization_id=1, name="Hosting"),
            ServiceTable(id=3, organization_id=1, name="Soporte"),
        ]

        service = _make_service(sql_repo=sql_repo)
        request = _create_request(
            service_items=[
                DocumentServiceItemRequest(
                    service_id=2,
                    value=100.0,
                    currency=CurrencyType.USD,
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 2, 1),
                ),
                DocumentServiceItemRequest(
                    service_id=3,
                    value=120.0,
                    currency=CurrencyType.EUR,
                    start_date=date(2024, 2, 2),
                    end_date=date(2024, 3, 1),
                ),
            ]
        )

        with pytest.raises(DocumentValidationError, match="misma moneda"):
            await service.create_document(request, _file_request(), organization_id=1)


class TestGetDocuments:
    @pytest.mark.asyncio
    async def test_get_documents_returns_all(self):
        docs = [_make_doc(1), _make_doc(2)]
        sql_repo = AsyncMock()
        sql_repo.get_all.return_value = docs

        service = _make_service(sql_repo=sql_repo)
        result = await service.get_documents(organization_id=1)

        assert result == docs
        sql_repo.get_all.assert_called_once_with(filters={"organization_id": 1})

    @pytest.mark.asyncio
    async def test_get_document_returns_doc_for_same_org(self):
        doc = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc

        service = _make_service(sql_repo=sql_repo)
        result = await service.get_document(1, organization_id=1)

        assert result == doc

    @pytest.mark.asyncio
    async def test_get_document_other_org_returns_none(self):
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = _make_doc(organization_id=2)

        service = _make_service(sql_repo=sql_repo)
        result = await service.get_document(1, organization_id=1)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_services_returns_catalog(self):
        services = [ServiceTable(id=1, organization_id=1, name="Hosting")]
        sql_repo = AsyncMock()
        sql_repo.get_services.return_value = services

        service = _make_service(sql_repo=sql_repo)
        result = await service.list_services(organization_id=1)

        assert result == services
        sql_repo.get_services.assert_called_once_with(organization_id=1)


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
        result = await service.delete_document(1, organization_id=1)

        assert result is True
        vector_repo.delete_vectors.assert_called_once()
        storage_repo.delete_file.assert_called_once_with(path=doc.file_path)

    @pytest.mark.asyncio
    async def test_delete_document_not_found_raises(self):
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = None

        service = _make_service(sql_repo=sql_repo)
        with pytest.raises(DocumentNotFoundError):
            await service.delete_document(99, organization_id=1)


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
        result = await service.update_document(1, UpdateDocumentRequest(name="Nuevo Nombre"), organization_id=1)

        assert result.name == "Nuevo Nombre"
        sql_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_replaces_service_items_when_provided(self):
        doc = _make_doc()
        updated = _make_doc()

        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc
        sql_repo.update.return_value = updated
        sql_repo.get_services_by_ids.return_value = [ServiceTable(id=3, organization_id=1, name="Mesa de ayuda")]

        service = _make_service(sql_repo=sql_repo)
        request = UpdateDocumentRequest(
            service_items=[
                DocumentServiceItemRequest(
                    service_id=3,
                    value=500.0,
                    currency=CurrencyType.USD,
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 3, 31),
                )
            ]
        )

        await service.update_document(1, request, organization_id=1)

        sql_repo.replace_document_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_recalculates_form_data_when_service_items_are_provided(self):
        doc = _make_doc()
        updated = _make_doc()

        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc
        sql_repo.update.return_value = updated
        sql_repo.get_services_by_ids.return_value = [ServiceTable(id=3, organization_id=1, name="Mesa de ayuda")]

        service = _make_service(sql_repo=sql_repo)
        request = UpdateDocumentRequest(
            service_items=[
                DocumentServiceItemRequest(
                    service_id=3,
                    value=400.0,
                    currency=CurrencyType.USD,
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 3, 31),
                )
            ]
        )

        await service.update_document(1, request, organization_id=1)

        updated_entity = sql_repo.update.await_args.kwargs["entity"]
        assert updated_entity.form_data["value"] == 400.0
        assert updated_entity.form_data["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_update_document_not_found_raises(self):
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = None

        service = _make_service(sql_repo=sql_repo)
        with pytest.raises(DocumentNotFoundError):
            await service.update_document(99, UpdateDocumentRequest(name="X"), organization_id=1)

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
        result = await service.update_document(1, UpdateDocumentRequest(), organization_id=1, file_data=file_data)

        assert result.file_path == "docs/1/new.pdf"
        storage_repo.delete_file.assert_called_once_with(path="docs/1/file.pdf")


class TestGetDocumentSignedUrl:
    @pytest.mark.asyncio
    async def test_returns_signed_url(self):
        doc = _make_doc()
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc
        storage_repo = AsyncMock()
        storage_repo.create_signed_url.return_value = "https://storage/signed"

        service = _make_service(sql_repo=sql_repo, storage_repo=storage_repo)
        url = await service.get_document_signed_url(1, organization_id=1)

        assert url == "https://storage/signed"

    @pytest.mark.asyncio
    async def test_document_not_found_raises(self):
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = None

        service = _make_service(sql_repo=sql_repo)
        with pytest.raises(DocumentNotFoundError):
            await service.get_document_signed_url(99, organization_id=1)

    @pytest.mark.asyncio
    async def test_document_without_file_raises(self):
        doc = _make_doc(file_path=None)
        sql_repo = AsyncMock()
        sql_repo.get_by_id.return_value = doc

        service = _make_service(sql_repo=sql_repo)
        with pytest.raises(DocumentFileMissingError):
            await service.get_document_signed_url(1, organization_id=1)
