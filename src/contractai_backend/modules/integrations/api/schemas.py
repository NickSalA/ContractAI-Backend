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

class DriveRequest(BaseModel):
    token: dict

class ImportRequest(BaseModel):
    token: dict
    file_ids: list[str]
    organization_id: int