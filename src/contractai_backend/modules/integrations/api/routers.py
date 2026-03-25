from typing import Annotated
from fastapi import APIRouter, Depends, Response

from contractai_backend.modules.integrations.api.dependencies import get_integration_service
from contractai_backend.modules.integrations.application.services.integration_service import IntegrationService
from contractai_backend.modules.integrations.api.schemas import AuthURLResponse, TokenResponse, FileListResponse, DriveFile, DriveRequest

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

@router.post("/list", response_model=FileListResponse)
async def list_drive_files(request: DriveRequest, service: IntegrationServiceDep):
    files = await service.fetch_folder_contents(token=request.token, folder_id=request.folder_id)
    drive_files = [DriveFile(id=f["id"], name=f["name"], mime_type=f["mimeType"]) for f in files]
    return FileListResponse(files=drive_files)

@router.post("/download/{file_id}")
async def download_drive_file(file_id: str, request: DriveRequest, service: IntegrationServiceDep):
    file_bytes = await service.retrieve_file(token=request.token, file_id=file_id)
    return Response(content=file_bytes, media_type="application/octet-stream")