from uuid import UUID

import httpx

from contractai_backend.core.exceptions.base import BadGatewayError, UnauthorizedError
from contractai_backend.shared.config import settings


class SupabaseAuthService:
    def __init__(self):
        self.base_url = settings.SUPABASE_URL.rstrip("/")
        self.api_key = settings.SUPABASE_SECRET_KEY

    async def get_authenticated_user(self, access_token: str) -> dict:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "apikey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/auth/v1/user", headers=headers)
        except httpx.RequestError as exc:
            raise BadGatewayError("No se pudo validar la sesión con Supabase Auth") from exc

        if response.status_code in (401, 403):
            raise UnauthorizedError("Token de autenticación inválido o expirado")

        if response.status_code != 200:
            raise BadGatewayError("Supabase Auth devolvió una respuesta inesperada")

        payload = response.json()
        if not payload.get("email") or not payload.get("id"):
            raise UnauthorizedError("La sesión autenticada no contiene los datos mínimos del usuario")

        return payload

    @staticmethod
    def parse_user_id(raw_user_id: str) -> UUID:
        try:
            return UUID(raw_user_id)
        except ValueError as exc:
            raise UnauthorizedError("El identificador del usuario autenticado no es válido") from exc
