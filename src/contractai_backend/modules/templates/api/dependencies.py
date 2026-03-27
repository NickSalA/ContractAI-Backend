"""Módulo de dependencias para el API de plantillas."""

from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from ....shared.infrastructure.database import get_session
from ...documents.api.dependencies import get_document_service
from ...documents.application.services import DocumentService
from ...organizations.api.dependencies import get_organization_service
from ...organizations.application.services.organization_service import OrganizationService
from ..application.repositories import IDocumentGenerator, IDocumentModuleAdapter, IOrganizationRepository, ITemplateRenderer, ITemplateRepository
from ..application.services.template_service import TemplateService
from ..infrastructure import DocumentModuleAdapter, JinjaRenderer, OrganizationModuleAdapter, SQLModelTemplateRepository, WeasyPrintGenerator

SessionDep = Annotated[AsyncSession, Depends(get_session)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
OrganizationDep = Annotated[OrganizationService, Depends(get_organization_service)]


async def get_template_repository(session: SessionDep) -> ITemplateRepository:
    """Devuelve una instancia del repositorio de plantillas."""
    return SQLModelTemplateRepository(session=session)


async def get_document_module_adapter(doc_service: DocumentServiceDep) -> IDocumentModuleAdapter:
    """Devuelve una instancia del adaptador del módulo de documentos."""
    return DocumentModuleAdapter(doc_service=doc_service)


async def get_organization_repository(org_service: OrganizationDep) -> IOrganizationRepository:
    """Devuelve una instancia del repositorio de organizaciones."""
    return OrganizationModuleAdapter(org_service=org_service)


async def get_template_renderer() -> ITemplateRenderer:
    """Devuelve una instancia del renderizador de plantillas."""
    return JinjaRenderer()


async def get_document_generator() -> IDocumentGenerator:
    """Devuelve una instancia del generador de documentos."""
    return WeasyPrintGenerator()


TemplateRepositoryDep = Annotated[ITemplateRepository, Depends(get_template_repository)]
DocumentAdapterDep = Annotated[IDocumentModuleAdapter, Depends(get_document_module_adapter)]
OrganizationRepositoryDep = Annotated[IOrganizationRepository, Depends(get_organization_repository)]
TemplateRendererDep = Annotated[ITemplateRenderer, Depends(get_template_renderer)]
DocumentGeneratorDep = Annotated[IDocumentGenerator, Depends(get_document_generator)]


async def get_template_service(
    template_repo: TemplateRepositoryDep,
    document_adapter: DocumentAdapterDep,
    organization_repo: OrganizationRepositoryDep,
    renderer: TemplateRendererDep,
    generator: DocumentGeneratorDep,
) -> TemplateService:
    """Devuelve una instancia del servicio de plantillas."""
    return TemplateService(
        template_repo=template_repo,
        document_adapter=document_adapter,
        organization_repo=organization_repo,
        renderer=renderer,
        document_generator=generator,
    )
