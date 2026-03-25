"""Módulo de Dependencias para el API de Usuarios."""

from typing import Annotated

from fastapi import Depends, Header
from sqlmodel.ext.asyncio.session import AsyncSession

from ....core.exceptions.base import UnauthorizedError
from ....shared.infrastructure.database import get_session
from ...users.application.repositories.user_repo import IUserRepository
from ..application.repositories.token_service import IAuthRepository
from ..application.services.auth_service import AuthService
from ..domain.entities import UserTable
from ..infrastructure.jwt_service import SupabaseAuthService
from ..infrastructure.postgres_repo import SQLModelUserRepository


async def get_user_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> IUserRepository:
    """Inyecta la implementación concreta del repositorio de usuarios."""
    return SQLModelUserRepository(session=session)


def get_identity_provider() -> IAuthRepository:
    """Inyecta el proveedor de identidad (Supabase)."""
    return SupabaseAuthService()


def get_auth_application_service(
    identity_provider: Annotated[IAuthRepository, Depends(get_identity_provider)], user_repo: Annotated[IUserRepository, Depends(get_user_repository)]
) -> AuthService:
    """Inyecta el servicio de aplicación que orquesta la autenticación."""
    return AuthService(jwt_service=identity_provider, repo=user_repo)


def extract_bearer_token(authorization: str | None = Header(default=None)) -> str:
    """Extrae el token del header Authorization."""
    if not authorization:
        raise UnauthorizedError("Falta el token de autenticación")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("Formato de token inválido")
    return token


async def get_current_user(
    token: Annotated[str, Depends(extract_bearer_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_application_service)],
) -> UserTable:
    """Obtiene el usuario autenticado delegando toda la lógica de validación, sincronización y persistencia al servicio de aplicación."""
    return await auth_service.authenticate_user(token)


CurrentUserDep = Annotated[UserTable, Depends(get_current_user)]
