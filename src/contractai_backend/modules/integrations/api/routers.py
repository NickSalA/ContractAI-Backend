from typing import Annotated
from fastapi import APIRouter, Depends, Response, BackgroundTasks

from contractai_backend.modules.integrations.api.dependencies import get_integration_service
from contractai_backend.modules.integrations.application.services.integration_service import IntegrationService
from contractai_backend.modules.integrations.api.schemas import AuthURLResponse, TokenResponse, DriveRequest, ImportRequest

router = APIRouter(prefix="/drive", tags=["Integrations"])
IntegrationServiceDep = Annotated[IntegrationService, Depends(get_integration_service)]

@router.get("/auth-url", response_model=AuthURLResponse)
async def get_authorization_url(service: IntegrationServiceDep):
    url = service.get_authorization_url()
    return AuthURLResponse(url=url)

@router.get("/callback", response_model=TokenResponse)
async def oauth_callback(code: str, service: IntegrationServiceDep):
    token_data = await service.authenticate(code=code)
    return TokenResponse(**token_data)

@router.post("/download/{file_id}")
async def download_drive_file(file_id: str, request: DriveRequest, service: IntegrationServiceDep):
    file_bytes = await service.retrieve_file(token=request.token, file_id=file_id)
    return Response(content=file_bytes, media_type="application/octet-stream")

@router.post("/import")
async def import_drive_files(request: ImportRequest, background_tasks: BackgroundTasks, service: IntegrationServiceDep):
    background_tasks.add_task(service.process_import, request.token, request.file_ids, request.organization_id)
    return {"message": "La importación ha comenzado en segundo plano."}