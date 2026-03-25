from contractai_backend.modules.integrations.application.repositories.base_integration import ICloudIntegrationProvider

class IntegrationService:
    def __init__(self, provider: ICloudIntegrationProvider):
        self.provider = provider

    def get_authorization_url(self) -> str:
        return self.provider.get_auth_url()

    async def authenticate(self, code: str) -> dict:
        return await self.provider.exchange_code_for_token(code)

    async def fetch_folder_contents(self, token: dict, folder_id: str | None = None) -> list[dict]:
        return await self.provider.list_files(token, folder_id)

    async def retrieve_file(self, token: dict, file_id: str) -> bytes:
        return await self.provider.download_file(token, file_id)