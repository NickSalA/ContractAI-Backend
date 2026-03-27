from fastapi import Depends

from contractai_backend.modules.documents.api.dependencies import get_document_service
from contractai_backend.modules.documents.application.services import DocumentService
from contractai_backend.modules.integrations.application import IntegrationService
from contractai_backend.modules.integrations.infrastructure import DocumentIngestionAdapter, GoogleDriveProvider
from contractai_backend.shared.config import settings


def get_cloud_storage_provider() -> GoogleDriveProvider:
    return GoogleDriveProvider(
        client_id=settings.GOOGLE_CLIENT_ID, client_secret=settings.GOOGLE_CLIENT_SECRET, redirect_uri=settings.GOOGLE_REDIRECT_URI
    )


def get_document_ingestion_target(document_service: DocumentService = Depends(get_document_service)) -> DocumentIngestionAdapter:
    return DocumentIngestionAdapter(document_service=document_service)


def get_integration_service(
    provider: GoogleDriveProvider = Depends(get_cloud_storage_provider),
    ingestion_target: DocumentIngestionAdapter = Depends(get_document_ingestion_target),
) -> IntegrationService:
    return IntegrationService(provider=provider, ingestion_target=ingestion_target, index_name=settings.DRIVE_INDEX_NAME)
