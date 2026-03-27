from fastapi import Depends

from contractai_backend.modules.integrations.application import IntegrationService
from contractai_backend.modules.integrations.infrastructure import GoogleDriveProvider
from contractai_backend.shared.config import settings


def get_cloud_storage_provider() -> GoogleDriveProvider:
    return GoogleDriveProvider(
        client_id=settings.GOOGLE_CLIENT_ID, client_secret=settings.GOOGLE_CLIENT_SECRET, redirect_uri=settings.GOOGLE_REDIRECT_URI
    )


def get_integration_service(provider: GoogleDriveProvider = Depends(get_cloud_storage_provider)) -> IntegrationService:
    return IntegrationService(provider=provider)
