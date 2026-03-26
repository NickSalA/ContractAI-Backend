"""Dependency providers for organizations."""

from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.modules.organizations.application.repositories.base_organization import OrganizationRepository
from contractai_backend.modules.organizations.application.services.organization_service import OrganizationService
from contractai_backend.modules.organizations.infrastructure.postgres_repo import SQLModelOrganizationRepository
from contractai_backend.shared.infrastructure.database import get_session


async def get_organization_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> OrganizationRepository:
    """Provide the concrete organization repository."""
    return SQLModelOrganizationRepository(session=session)


async def get_organization_service(
    repository: Annotated[OrganizationRepository, Depends(get_organization_repository)],
) -> OrganizationService:
    """Provide the organizations application service."""
    return OrganizationService(repository=repository)
