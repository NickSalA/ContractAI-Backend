""""Dependencia para extraer el token Bearer del header de autorización."""

from fastapi import Header

from ....core.exceptions.base import UnauthorizedError


def get_token(authorization: str | None = Header(default=None)) -> str:
    """Extrae el token del header 'Authorization: Bearer <token>'."""
    if not authorization:
        raise UnauthorizedError("No se proporcionó un token de autenticación")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("El formato del token debe ser 'Bearer <token>'")

    return token
