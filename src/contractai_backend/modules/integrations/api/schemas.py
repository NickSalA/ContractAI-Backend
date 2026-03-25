from pydantic import BaseModel

class AuthURLResponse(BaseModel):
    url: str

class TokenResponse(BaseModel):
    token: str
    refresh_token: str | None
    token_uri: str
    client_id: str
    client_secret: str
    scopes: list[str]

class DriveFile(BaseModel):
    id: str
    name: str
    mime_type: str

class FileListResponse(BaseModel):
    files: list[DriveFile]

class DriveRequest(BaseModel):
    token: dict
    folder_id: str | None = None