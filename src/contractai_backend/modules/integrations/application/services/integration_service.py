import asyncio
from loguru import logger
from contractai_backend.modules.integrations.application.repositories.base_integration import ICloudIntegrationProvider
from contractai_backend.modules.integrations.domain.exceptions import (
    CloudStorageIntegrationError,
    InvalidCloudTokenError,
    CloudFileNotFoundError
)


class IntegrationService:
    def __init__(self, provider: ICloudIntegrationProvider):
        self.provider = provider

    def get_authorization_url(self) -> str:
        return self.provider.get_auth_url()

    async def authenticate(self, code: str) -> dict:
        return await self.provider.exchange_code_for_token(code)

    async def retrieve_file(self, token: dict, file_id: str) -> bytes:
        return await self.provider.download_file(token, file_id)

    async def process_import(self, token: dict, file_ids: list[str], organization_id: int) -> None:
        logger.info(f"Iniciando importación directa. Organización: {organization_id}. Archivos: {len(file_ids)}")

        for file_id in file_ids:
            try:
                metadata = await self.provider.get_file_metadata(token, file_id)
                file_name = metadata.get('name', 'documento_desconocido')
                web_link = metadata.get('webViewLink', '')

                logger.debug(f"Extrayendo metadatos de: {file_name} | Link: {web_link}")

                file_bytes = await self.retrieve_file(token, file_id)

                logger.success(f"¡Extracción exitosa! Archivo: {file_name} | Tamaño: {len(file_bytes)} bytes")

                await asyncio.sleep(1)

            except InvalidCloudTokenError as e:
                logger.error(f"Fallo de autenticación en la importación. Token inválido o expirado. Organización: {organization_id}. Error: {e}")
                break  # Si el token es inválido, abortamos todo el proceso para evitar un alud de errores
            except CloudFileNotFoundError as e:
                logger.warning(f"Archivo no encontrado {file_id}. Se saltará. Error: {e}")
                continue
            except CloudStorageIntegrationError as e:
                logger.error(f"Fallo al comunicarse con Google Drive para el archivo {file_id}. Error: {e}")
                continue
            except Exception as e:
                logger.error(f"Fallo crítico al importar el archivo {file_id}. Error: {e}")
                continue

        logger.info("Proceso de importación finalizado.")