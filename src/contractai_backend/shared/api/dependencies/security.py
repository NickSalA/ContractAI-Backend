"""Dependencias de seguridad para la API."""

from typing import Annotated, Any

from fastapi import Depends

from ....modules.users.api.dependencies import get_auth_application_service
from ....modules.users.domain.entities import UserTable
from .bearer import get_token


async def get_current_user(
    token: Annotated[str, Depends(get_token)],
    auth_service: Annotated[Any, Depends(get_auth_application_service)],
) -> UserTable:
    """Dependencia de seguridad global.

    Valida el token con Supabase y sincroniza/registra al usuario en la DB.
    """
    return await auth_service.authenticate_user(token)


CurrentUserDep = Annotated[UserTable, Depends(get_current_user)]
