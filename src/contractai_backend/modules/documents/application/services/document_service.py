"""DocumentService: Orchestrates document creation and storage across repositories."""

from collections.abc import Sequence
from datetime import UTC, date, datetime
from typing import Any

from loguru import logger
from pydantic import ValidationError as PydanticValidationError

from ...api.schemas import (
    CreateDocumentRequest,
    DocumentServiceItemRequest,
    FileRequest,
    UpdateDocumentRequest,
    DocumentResponse,
    DocumentServiceItemResponse,
)
from ...domain.entities import DocumentServiceTable, DocumentTable, ServiceTable
from ...domain.exceptions import (
    DocumentExtractionError,
    DocumentFileMissingError,
    DocumentNotFoundError,
    DocumentTransactionError,
    DocumentValidationError,
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

    @staticmethod
    def _build_validation_message(exc: PydanticValidationError) -> str:
        messages = []
        for error in exc.errors():
            field = error.get("loc", ["documento"])[0]
            messages.append(f"{field}: {error.get('msg')}")
        return "; ".join(messages)

    def _validate_document(self, payload: dict) -> DocumentTable:
        try:
            return DocumentTable.model_validate(obj=payload)
        except PydanticValidationError as exc:
            raise DocumentValidationError(self._build_validation_message(exc)) from exc

    @staticmethod
    def _build_document_service_entities(document_id: int, service_items: Sequence[DocumentServiceItemRequest]) -> list[DocumentServiceTable]:
        return [
            DocumentServiceTable(
                document_id=document_id,
                service_id=item.service_id,
                description=item.description,
                value=item.value,
                currency=item.currency,
                start_date=item.start_date,
                end_date=item.end_date,
            )
            for item in service_items
        ]

    @staticmethod
    def _build_form_data_payload(base_form_data: dict[str, Any], service_items: Sequence[DocumentServiceItemRequest]) -> dict[str, Any]:
        payload = dict(base_form_data)
        payload.pop("licenses", None)

        if service_items:
            payload["value"] = sum(item.value for item in service_items)
            payload["currency"] = service_items[0].currency.value

        return payload

    @staticmethod
    def _enrich_vector_chunks(chunks: Sequence[Any], organization_id: int, form_data: dict[str, Any]) -> None:
        source_metadata = form_data.get("source") if isinstance(form_data, dict) else None

        for chunk in chunks:
            metadata = getattr(chunk, "metadata", None)
            if metadata is None:
                metadata = {}
                setattr(chunk, "metadata", metadata)

            metadata["organization_id"] = str(organization_id)

            if isinstance(source_metadata, dict):
                provider = source_metadata.get("provider")
                file_id = source_metadata.get("file_id")

                if provider:
                    metadata["source_provider"] = str(provider)
                if file_id:
                    metadata["source_file_id"] = str(file_id)

    async def _build_document_response(self, document: DocumentTable) -> DocumentResponse:
        """Busca los servicios asociados y ensambla el DTO final."""
        service_items = []
        if document.id is not None:
            service_items = await self.sql_repo.get_document_services(document_id=document.id)

        return self._serialize_document_response(document=document, service_items=service_items)

    @staticmethod
    def _serialize_document_response(document: DocumentTable, service_items: Sequence[DocumentServiceTable] | None = None) -> DocumentResponse:
        """Mapea las entidades de BD al esquema de Pydantic."""
        resolved_service_items = list(service_items or [])

        return DocumentResponse(
            id=document.id,
            name=document.name,
            client=document.client,
            type=document.type,
            start_date=document.start_date,
            end_date=document.end_date,
            form_data=document.form_data,
            state=document.state,
            file_path=document.file_path,
            file_name=document.file_name,
            service_items=[DocumentServiceItemResponse.model_validate(item) for item in resolved_service_items],
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def _validate_service_periods(
        document_start_date: date,
        document_end_date: date,
        service_items: Sequence[DocumentServiceItemRequest],
    ) -> None:
        for item in service_items:
            if item.start_date < document_start_date or item.end_date > document_end_date:
                raise DocumentValidationError(message=(f"El servicio {item.service_id} debe tener fechas dentro del rango del contrato."))

    @staticmethod
    def _validate_service_currency_alignment(service_items: Sequence[DocumentServiceItemRequest]) -> None:
        currencies = {item.currency for item in service_items}
        if len(currencies) > 1:
            raise DocumentValidationError(message="Todos los servicios asociados al contrato deben usar la misma moneda.")

    async def _validate_requested_services(self, organization_id: int, service_items: Sequence[DocumentServiceItemRequest]) -> None:
        if not service_items:
            return

        requested_ids = [item.service_id for item in service_items]
        existing_services = await self.sql_repo.get_services_by_ids(organization_id=organization_id, service_ids=requested_ids)
        existing_ids = {service.id for service in existing_services if service.id is not None}
        missing_ids = sorted(set(requested_ids) - existing_ids)

        if missing_ids:
            raise DocumentValidationError(message=f"Los servicios con IDs {missing_ids} no existen o no pertenecen a la organización actual.")

    async def _get_document_entity(self, id: int, organization_id: int) -> DocumentTable | None:
        """Obtiene la entidad ORM cruda de la base de datos (solo para uso interno)."""
        doc = await self.sql_repo.get_by_id(id)
        if doc is None or doc.organization_id != organization_id:
            return None
        return doc

    async def list_services(self, organization_id: int) -> Sequence[ServiceTable]:
        """Returns the service catalog for the current organization."""
        return await self.sql_repo.get_services(organization_id=organization_id)

    async def create_document(
        self,
        data: CreateDocumentRequest,
        file_data: FileRequest,
        organization_id: int,
        index_name: str = "contracts_index",
    ) -> DocumentResponse:
        """Creates a new document, orchestrating SQL, Storage, and Vector DB."""
        await self._validate_requested_services(organization_id=organization_id, service_items=data.service_items)
        self._validate_service_currency_alignment(service_items=data.service_items)
        self._validate_service_periods(
            document_start_date=data.start_date,
            document_end_date=data.end_date,
            service_items=data.service_items,
        )

        normalized_form_data = self._build_form_data_payload(base_form_data=data.form_data, service_items=data.service_items)

        new_document = self._validate_document(
            {
                "name": data.name,
                "organization_id": organization_id,
                "client": data.client,
                "type": data.type,
                "start_date": data.start_date,
                "end_date": data.end_date,
                "form_data": normalized_form_data,
                "state": data.state,
            }
        )

        parsed_document = await self.extractor.extract(file=file_data.content, filename=file_data.filename)
        if not parsed_document:
            raise DocumentExtractionError()

        self._enrich_vector_chunks(chunks=parsed_document, organization_id=organization_id, form_data=normalized_form_data)

        save_doc: DocumentTable = await self.sql_repo.save(entity=new_document)

        if not save_doc.id:
            raise DocumentTransactionError(operation="create", details="Failed to save document in SQL, no ID returned")

        document_id: int = save_doc.id
        service_entities = self._build_document_service_entities(document_id=document_id, service_items=data.service_items)

        storage_path = None
        vectors_added = False

        try:
            await self.sql_repo.replace_document_services(document_id=document_id, service_items=service_entities)

            storage_path = await self.storage_repo.upload_file(
                document_id=document_id,
                file=file_data.content,
                filename=file_data.filename,
                content_type=file_data.content_type,
            )

            await self.vector_repo.add_vectors(index_name=index_name, document_id=document_id, chunks=parsed_document)
            vectors_added = True

            save_doc.file_path = storage_path
            save_doc.file_name = file_data.filename
            updated_saved_doc: DocumentTable = await self.sql_repo.update(entity=save_doc)

            return await self._build_document_response(document=updated_saved_doc)

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

    async def get_documents(self, organization_id: int) -> Sequence[DocumentResponse]:  # <-- Retorna DocumentResponse, no DocumentTable
        """Obtiene todos los documentos y los ensambla con sus servicios asociados."""
        docs: Sequence[DocumentTable] = await self.sql_repo.get_all(filters={"organization_id": organization_id})
        document_ids: list[int] = [doc.id for doc in docs if doc.id is not None]
        service_items_by_document = {}
        if document_ids:
            service_items_by_document = await self.sql_repo.get_document_services_by_document_ids(document_ids=document_ids)
        return [self._serialize_document_response(document=doc, service_items=service_items_by_document.get(doc.id, [])) for doc in docs]

    async def get_document(self, id: int, organization_id: int) -> DocumentResponse | None:
        """Retrieves a single document by ID from the relational repository."""
        doc = await self.sql_repo.get_by_id(id)
        if doc is None or doc.organization_id != organization_id:
            return None
        return await self._build_document_response(document=doc)

    async def delete_document(self, id: int, organization_id: int, index_name: str = "contracts_index") -> bool:
        """Deletes a document orchestrating SQL, VectorDB, and Storage."""
        doc: DocumentResponse | None = await self.get_document(id=id, organization_id=organization_id)
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
        organization_id: int,
        file_data: FileRequest | None = None,
        index_name: str = "contracts_index",
    ) -> DocumentResponse:
        """Updates an existing document orchestrating SQL, VectorDB, and Storage."""
        doc: DocumentTable | None = await self._get_document_entity(id=id, organization_id=organization_id)
        if not doc:
            raise DocumentNotFoundError(document_id=id)

        update_data = data.model_dump(exclude_unset=True)
        service_items_provided = "service_items" in update_data
        requested_service_items = data.service_items or []

        if service_items_provided:
            await self._validate_requested_services(
                organization_id=organization_id,
                service_items=requested_service_items,
            )
            self._validate_service_currency_alignment(service_items=requested_service_items)

        final_start_date = update_data.get("start_date", doc.start_date)
        final_end_date = update_data.get("end_date", doc.end_date)
        final_form_data = update_data.get("form_data", doc.form_data)

        if service_items_provided:
            self._validate_service_periods(
                document_start_date=final_start_date,
                document_end_date=final_end_date,
                service_items=requested_service_items,
            )
            final_form_data = self._build_form_data_payload(
                base_form_data=final_form_data,
                service_items=requested_service_items,
            )

        validated_doc = self._validate_document(
            {
                "id": doc.id,
                "organization_id": doc.organization_id,
                "name": update_data.get("name", doc.name),
                "client": update_data.get("client", doc.client),
                "type": update_data.get("type", doc.type),
                "start_date": final_start_date,
                "end_date": final_end_date,
                "form_data": final_form_data,
                "state": update_data.get("state", doc.state),
                "file_path": doc.file_path,
                "file_name": doc.file_name,
                "created_at": doc.created_at,
                "updated_at": datetime.now(UTC),
            }
        )

        doc.name = validated_doc.name
        doc.client = validated_doc.client
        doc.type = validated_doc.type
        doc.start_date = validated_doc.start_date
        doc.end_date = validated_doc.end_date
        doc.form_data = validated_doc.form_data
        doc.state = validated_doc.state
        doc.updated_at = validated_doc.updated_at

        if file_data is None:
            if service_items_provided and doc.id is not None:
                service_entities = self._build_document_service_entities(
                    document_id=doc.id,
                    service_items=requested_service_items,
                )
                await self.sql_repo.replace_document_services(document_id=doc.id, service_items=service_entities)
            updated_doc = await self.sql_repo.update(entity=doc)
            return await self._build_document_response(document=updated_doc)

        if not file_data.filename or file_data.content_type is None:
            raise InvalidDocumentFileError()

        parsed_document = await self.extractor.extract(file=file_data.content, filename=file_data.filename)
        if not parsed_document:
            raise DocumentExtractionError()

        self._enrich_vector_chunks(chunks=parsed_document, organization_id=organization_id, form_data=doc.form_data)

        old_storage_path = doc.file_path
        new_storage_path = None

        try:
            new_storage_path = await self.storage_repo.upload_file(
                document_id=id,
                file=file_data.content,
                filename=file_data.filename,
                content_type=file_data.content_type,
            )

            await self.vector_repo.add_vectors(index_name=index_name, document_id=id, chunks=parsed_document)

            doc.file_path = new_storage_path
            doc.file_name = file_data.filename
            doc.updated_at = datetime.now(UTC)

            if service_items_provided and doc.id is not None:
                service_entities = self._build_document_service_entities(
                    document_id=doc.id,
                    service_items=requested_service_items,
                )
                await self.sql_repo.replace_document_services(document_id=doc.id, service_items=service_entities)

            updated_doc = await self.sql_repo.update(entity=doc)

            if old_storage_path and old_storage_path != new_storage_path:
                try:
                    await self.storage_repo.delete_file(path=old_storage_path)
                except Exception:
                    pass

            return await self._build_document_response(document=updated_doc)

        except Exception as e:
            if new_storage_path:
                try:
                    await self.storage_repo.delete_file(path=new_storage_path)
                except Exception:
                    pass

            raise DocumentTransactionError(operation="update", details=str(object=e)) from e

    async def get_document_signed_url(self, id: int, organization_id: int, expires_in: int = 3600) -> str:
        """Returns a temporary signed URL for a stored document file."""
        doc: DocumentTable | None = await self._get_document_entity(id=id, organization_id=organization_id)
        if not doc:
            raise DocumentNotFoundError(document_id=id)
        if doc.file_path is None:
            raise DocumentFileMissingError(document_id=id)

        storage_path: str = doc.file_path
        return await self.storage_repo.create_signed_url(path=storage_path, expires_in=expires_in)
