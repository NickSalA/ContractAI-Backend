"""Supabase Storage implementation for document files."""

import asyncio
import json
from urllib import error, request

from ....shared.config import settings
from ..application.repositories import DocumentStorageRepository


class SupabaseStorageRepository(DocumentStorageRepository):
    """Stores document binaries in Supabase Storage using REST API."""

    def __init__(self):
        self.base_url = settings.SUPABASE_URL.rstrip("/")
        self.bucket = settings.SUPABASE_STORAGE_BUCKET
        self.api_key = settings.SUPABASE_SECRET_KEY

    async def upload_file(self, *, path: str, file: bytes, content_type: str) -> None:
        await asyncio.to_thread(self._upload_file_sync, path, file, content_type)

    async def delete_file(self, *, path: str) -> None:
        await asyncio.to_thread(self._delete_file_sync, path)

    async def create_signed_url(self, *, path: str, expires_in: int = 3600) -> str:
        return await asyncio.to_thread(self._create_signed_url_sync, path, expires_in)

    def _upload_file_sync(self, path: str, file: bytes, content_type: str) -> None:
        endpoint = f"{self.base_url}/storage/v1/object/{self.bucket}/{path}"
        req = request.Request(
            endpoint,
            data=file,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "apikey": self.api_key,
                "Content-Type": content_type,
                "x-upsert": "true",
            },
        )

        try:
            with request.urlopen(req) as response:
                if response.status not in (200, 201):
                    body = response.read().decode("utf-8", errors="ignore")
                    raise RuntimeError(f"Storage upload failed: {body}")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Storage upload failed ({exc.code}): {body}") from exc

    def _delete_file_sync(self, path: str) -> None:
        endpoint = f"{self.base_url}/storage/v1/object/{self.bucket}/{path}"
        req = request.Request(
            endpoint,
            method="DELETE",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "apikey": self.api_key,
            },
        )

        try:
            request.urlopen(req)
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            normalized_body = body.lower()

            object_not_found = (
                exc.code == 404
                or (exc.code == 400 and "not_found" in normalized_body)
                or (exc.code == 400 and "object not found" in normalized_body)
                or (exc.code == 400 and '"statuscode":"404"' in normalized_body)
            )

            if object_not_found:
                return
            raise RuntimeError(f"Storage delete failed ({exc.code}): {body}") from exc

    def _create_signed_url_sync(self, path: str, expires_in: int) -> str:
        endpoint = f"{self.base_url}/storage/v1/object/sign/{self.bucket}/{path}"
        payload = json.dumps({"expiresIn": expires_in}).encode("utf-8")

        req = request.Request(
            endpoint,
            method="POST",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "apikey": self.api_key,
                "Content-Type": "application/json",
            },
        )

        try:
            with request.urlopen(req) as response:
                body = response.read().decode("utf-8", errors="ignore")
                data = json.loads(body)

                signed_url = data.get("signedURL")
                if not signed_url:
                    raise RuntimeError(f"Invalid signed URL response: {body}")
                return f"{self.base_url}/storage/v1{signed_url}"
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Signed URL creation failed ({exc.code}): {body}") from exc
