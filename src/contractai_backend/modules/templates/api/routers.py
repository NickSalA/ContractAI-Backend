"""Módulo de enrutamiento para la API de plantillas."""

from contractai_backend.modules.templates.domain.entities import TemplateTable

from typing import Annotated, Any, Sequence

from fastapi import APIRouter, Depends, HTTPException, status

from ....shared.api.dependencies.security import CurrentUserDep
from ..application.services.template_service import TemplateService
from .dependencies import get_template_service

router = APIRouter()

TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]


@router.post(path="/{template_id}/generate", status_code=status.HTTP_201_CREATED)
async def generate_template(
    template_id: int,
    request: dict[str, Any],
    template_service: TemplateServiceDep,
    current_user: CurrentUserDep,
):
    """Endpoint para generar un documento a partir de una plantilla."""
    try:
        generated_document = await template_service.generate_contract(
            template_id=template_id, form_data=request, organization_id=current_user.organization_id
        )
        return generated_document
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al generar el documento: {e!s}") from e


@router.get(path="/{template_id}", status_code=status.HTTP_200_OK)
async def get_template(
    template_id: int,
    template_service: TemplateServiceDep,
    current_user: CurrentUserDep,
):
    """Endpoint para obtener los detalles de una plantilla."""
    try:
        template: TemplateTable | None = await template_service.get_template(template_id=template_id, organization_id=current_user.organization_id)
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla no encontrada")
        return template
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al obtener la plantilla: {e!s}") from e


@router.get(path="/", status_code=status.HTTP_200_OK)
async def list_templates(
    template_service: TemplateServiceDep,
    current_user: CurrentUserDep,
):
    """Endpoint para listar las plantillas de la organización."""
    try:
        templates: Sequence[TemplateTable] = await template_service.list_templates(organization_id=current_user.organization_id)
        return templates
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al listar las plantillas: {e!s}") from e
