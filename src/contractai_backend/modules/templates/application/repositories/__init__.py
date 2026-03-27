from .base_generate import IDocumentGenerator
from .base_relational import IDocumentModuleAdapter, IOrganizationRepository, ITemplateRepository
from .base_render import ITemplateRenderer

__all__ = [
    "IDocumentGenerator",
    "IDocumentModuleAdapter",
    "IOrganizationRepository",
    "ITemplateRenderer",
    "ITemplateRepository",
]
