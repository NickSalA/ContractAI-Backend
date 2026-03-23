"""Supabase Storage implementation for document files."""

import re

import httpx
from httpx._models import Response

from ....shared.config import settings
from ..application.repositories import DocumentStorageRepository
from ..domain.exceptions import DocumentStorageError, DocumentStorageUnavailableError


class SupabaseStorageRepository(DocumentStorageRepository):
    """Stores document binaries in Supabase Storage using REST API."""

    def __init__(self):
        self.base_url: str = settings.SUPABASE_URL.rstrip("/")
        self.bucket: str = settings.SUPABASE_STORAGE_BUCKET
        self.api_key: str = settings.SUPABASE_SECRET_KEY

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitizes filenames to a safe storage-friendly format."""
        base_name: str = filename.rsplit(sep="/", maxsplit=1)[-1].rsplit(sep="\\", maxsplit=1)[-1]
        normalized: str = re.sub(pattern=r"[^A-Za-z0-9._-]", repl="_", string=base_name).strip("._")
        if not normalized:
            return "document.pdf"
        if "." not in normalized:
            return f"{normalized}.pdf"
        return normalized

    def _build_path(self, document_id: int, filename: str | None = None) -> str:
        """Builds deterministic storage path for each document."""
        if not filename:
            return f"documents/{document_id}.pdf"
        safe_name: str = self._sanitize_filename(filename)
        return f"documents/{document_id}/{safe_name}"

    async def upload_file(self, document_id: int, file: bytes, filename: str, content_type: str) -> str:
        """Uploads a document file to Supabase Storage."""
        path: str = self._build_path(document_id, filename)
        endpoint = f"{self.base_url}/storage/v1/object/{self.bucket}/{path}"

        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "apikey": self.api_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        try:
            async with httpx.AsyncClient() as client:
                response: Response = await client.post(url=endpoint, content=file, headers=headers)

        except httpx.TimeoutException as e:
            raise DocumentStorageUnavailableError("El servicio de almacenamiento de documentos no respondió a tiempo.") from e
        except httpx.RequestError as e:
            raise DocumentStorageUnavailableError("No se pudo conectar al servicio de almacenamiento de documentos.") from e
        if response.status_code not in (httpx.codes.OK, httpx.codes.CREATED):
            raise DocumentStorageError("Fallo al subir el archivo al almacenamiento de documentos.")

        return path

    async def delete_file(self, path: str) -> None:
        """Deletes a document file from Supabase Storage if it exists."""
        endpoint = f"{self.base_url}/storage/v1/object/{self.bucket}/{path}"

        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "apikey": self.api_key,
        }
        try:
            async with httpx.AsyncClient() as client:
                response: Response = await client.delete(url=endpoint, headers=headers)
        except httpx.TimeoutException as e:
            raise DocumentStorageUnavailableError("El servicio de almacenamiento de documentos no respondió a tiempo.") from e
        except httpx.RequestError as e:
            raise DocumentStorageUnavailableError("No se pudo conectar al servicio de almacenamiento de documentos.") from e
        if response.status_code not in (httpx.codes.OK, httpx.codes.NO_CONTENT):
            normalized_body: str = response.text.lower()
            object_not_found = (
                response.status_code == httpx.codes.NOT_FOUND
                or (response.status_code == httpx.codes.BAD_REQUEST and "not_found" in normalized_body)
                or (response.status_code == httpx.codes.BAD_REQUEST and "object not found" in normalized_body)
            )

            if object_not_found:
                return

            raise DocumentStorageError("Fallo al eliminar el archivo del almacenamiento de documentos.")

    async def create_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """Creates a signed URL for temporary access to a document file."""
        endpoint = f"{self.base_url}/storage/v1/object/sign/{self.bucket}/{path}"

        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "apikey": self.api_key,
        }

        payload: dict[str, int] = {"expiresIn": expires_in}

        try:
            async with httpx.AsyncClient() as client:
                response: Response = await client.post(url=endpoint, json=payload, headers=headers)
        except httpx.TimeoutException as e:
            raise DocumentStorageUnavailableError("El servicio de almacenamiento de documentos no respondió a tiempo.") from e
        except httpx.RequestError as e:
            raise DocumentStorageUnavailableError("No se pudo conectar al servicio de almacenamiento de documentos.") from e

        if response.status_code != httpx.codes.OK:
            raise DocumentStorageError("Fallo al generar la URL firmada para el archivo del almacenamiento de documentos.")

        data = response.json()
        signed_url = data.get("signedURL")
        if not signed_url:
            raise DocumentStorageError("La respuesta del almacenamiento de documentos no contiene la URL firmada.")

        return f"{self.base_url}/storage/v1{signed_url}"
