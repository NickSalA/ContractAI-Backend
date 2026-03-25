from fastapi import APIRouter

from contractai_backend.modules.users.api.dependencies import CurrentUserDep
from contractai_backend.modules.users.api.schemas import CurrentUserResponse

router = APIRouter()


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: CurrentUserDep) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)
