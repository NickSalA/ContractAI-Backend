"""Supabase Storage implementation for document files."""

import re

import httpx

from ....shared.config import settings
from ..application.repositories import DocumentStorageRepository


class SupabaseStorageRepository(DocumentStorageRepository):
    """Stores document binaries in Supabase Storage using REST API."""

    def __init__(self):
        self.base_url = settings.SUPABASE_URL.rstrip("/")
        self.bucket = settings.SUPABASE_STORAGE_BUCKET
        self.api_key = settings.SUPABASE_SECRET_KEY

    def _sanitize_filename(self,filename: str) -> str:
        """Sanitizes filenames to a safe storage-friendly format."""
        base_name = filename.rsplit("/", maxsplit=1)[-1].rsplit("\\", maxsplit=1)[-1]
        normalized = re.sub(r"[^A-Za-z0-9._-]", "_", base_name).strip("._")
        if not normalized:
            return "document.pdf"
        if "." not in normalized:
            return f"{normalized}.pdf"
        return normalized

    def _build_path(self, document_id: int, filename: str | None = None) -> str:
        """Builds deterministic storage path for each document."""
        if not filename:
            return f"documents/{document_id}.pdf"
        safe_name = self._sanitize_filename(filename)
        return f"documents/{document_id}/{safe_name}"

    async def upload_file(self, document_id: int, file: bytes, filename: str, content_type: str) -> str:
        """Uploads a document file to Supabase Storage."""
        path = self._build_path(document_id, filename)
        endpoint = f"{self.base_url}/storage/v1/object/{self.bucket}/{path}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "apikey": self.api_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, content=file, headers=headers)
            if response.status_code not in (httpx.codes.OK, httpx.codes.CREATED):
                raise RuntimeError(f"Storage upload failed: {response.text}")

        return path

    async def delete_file(self, path: str) -> None:
        """Deletes a document file from Supabase Storage if it exists."""
        endpoint = f"{self.base_url}/storage/v1/object/{self.bucket}/{path}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "apikey": self.api_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.delete(endpoint, headers=headers)

            if response.status_code not in (httpx.codes.OK, httpx.codes.NO_CONTENT):
                normalized_body = response.text.lower()
                object_not_found = (
                    response.status_code == httpx.codes.NOT_FOUND
                    or (response.status_code == httpx.codes.BAD_REQUEST and "not_found" in normalized_body)
                    or (response.status_code == httpx.codes.BAD_REQUEST and "object not found" in normalized_body)
                )

                if object_not_found:
                    return
                raise RuntimeError(f"Storage delete failed ({response.status_code}): {response.text}")

    async def create_signed_url(self, *, path: str, expires_in: int = 3600) -> str:
        """Creates a signed URL for temporary access to a document file."""
        endpoint = f"{self.base_url}/storage/v1/object/sign/{self.bucket}/{path}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "apikey": self.api_key,
        }

        payload = {"expiresIn": expires_in}

        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            if response.status_code != httpx.codes.OK:
                raise RuntimeError(f"Signed URL creation failed ({response.status_code}): {response.text}")
            data = response.json()
            signed_url = data.get("signedURL")
            if not signed_url:
                raise RuntimeError(f"Invalid signed URL response: {response.text}")

            return f"{self.base_url}/storage/v1{signed_url}"
