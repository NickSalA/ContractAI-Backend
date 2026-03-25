from typing import Annotated

from fastapi import Depends, Header
from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.core.exceptions.base import ForbiddenError, UnauthorizedError
from contractai_backend.modules.users.domain.entities import UserTable
from contractai_backend.modules.users.infrastructure.jwt_service import SupabaseAuthService
from contractai_backend.modules.users.infrastructure.supabase_repo import SQLModelUserRepository
from contractai_backend.shared.infrastructure.database import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_user_repository(session: SessionDep) -> SQLModelUserRepository:
    return SQLModelUserRepository(session=session)


def get_auth_service() -> SupabaseAuthService:
    return SupabaseAuthService()


UserRepositoryDep = Annotated[SQLModelUserRepository, Depends(get_user_repository)]
AuthServiceDep = Annotated[SupabaseAuthService, Depends(get_auth_service)]


def extract_bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise UnauthorizedError("Falta el token de autenticación")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("El encabezado Authorization debe usar el esquema Bearer")
    return token


BearerTokenDep = Annotated[str, Depends(extract_bearer_token)]


async def get_current_user(
    token: BearerTokenDep,
    auth_service: AuthServiceDep,
    repository: UserRepositoryDep,
) -> UserTable:
    auth_user = await auth_service.get_authenticated_user(token)
    email = auth_user["email"].strip().lower()
    supabase_user_id = auth_service.parse_user_id(auth_user["id"])
    user_metadata = auth_user.get("user_metadata") or {}

    user = await repository.get_by_email(email)
    if user is None or not user.is_active:
        raise ForbiddenError("Acceso denegado para este usuario")

    if user.supabase_user_id and user.supabase_user_id != supabase_user_id:
        raise ForbiddenError("La cuenta autenticada no coincide con el usuario registrado")

    updates: dict[str, object] = {}
    if user.supabase_user_id is None:
        updates["supabase_user_id"] = supabase_user_id
    if user_metadata.get("full_name") and user.full_name != user_metadata["full_name"]:
        updates["full_name"] = user_metadata["full_name"]
    if user_metadata.get("avatar_url") and user.avatar_url != user_metadata["avatar_url"]:
        updates["avatar_url"] = user_metadata["avatar_url"]

    if updates:
        user = await repository.update_fields(user, **updates)

    return user


CurrentUserDep = Annotated[UserTable, Depends(get_current_user)]
