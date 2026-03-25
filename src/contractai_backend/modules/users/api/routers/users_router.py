"""Router de usuarios."""

from fastapi import APIRouter

from contractai_backend.modules.users.api.schemas import CurrentUserResponse

from .....shared.api.dependencies.security import CurrentUserDep

router = APIRouter()


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: CurrentUserDep) -> CurrentUserResponse:
    """Endpoint para obtener los datos del usuario autenticado."""
    return CurrentUserResponse.model_validate(current_user)
