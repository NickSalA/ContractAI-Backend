"""Adaptador que conecta el módulo de templates con el servicio de organizaciones para obtener datos necesarios durante el renderizado."""

from typing import Any

from contractai_backend.modules.organizations.domain.entities import OrganizationTable

from ...organizations.application.services.organization_service import OrganizationService
from ..application.repositories.base_relational import IOrganizationRepository


class OrganizationModuleAdapter(IOrganizationRepository):
    def __init__(self, org_service: OrganizationService):
        self.org_service: OrganizationService = org_service

    async def get_organization_data(self, organization_id: int) -> dict[str, Any]:
        """Obtiene los datos de la organización necesarios para el renderizado de plantillas."""
        org_entity: OrganizationTable = await self.org_service.get_organization(organization_id=organization_id)
        if not org_entity:
            raise ValueError("Organization not found.")
        return {
            "empleador_razon_social": org_entity.name,
            "empleador_ruc": getattr(org_entity, "ruc", ""),
            "empleador_domicilio": getattr(org_entity, "address", ""),
            "empleador_descripcion": getattr(org_entity, "company_type", ""),
            "empleador_objeto_social": getattr(org_entity, "objeto_social", ""),
            "representante_nombre": getattr(org_entity, "legal_rep_name", ""),
            "representante_dni": getattr(org_entity, "legal_rep_dni", ""),
            "jurisdiccion": getattr(org_entity, "jurisdiction", "Lima"),
            "lugar_firma": getattr(org_entity, "city", "Lima"),
            "autorizacion_entidad": getattr(org_entity, "autorizacion_entidad", ""),
            "autorizacion_fecha": getattr(org_entity, "autorizacion_fecha", ""),
            "autorizacion_emitida_por": getattr(org_entity, "autorizacion_emitida_por", ""),
            "empleador_email": getattr(org_entity, "email", ""),
            "empleador_telefono": getattr(org_entity, "phone", ""),
        }
