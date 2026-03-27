"""Módulo encargado de renderizar las plantillas Markdown utilizando Jinja2."""

from typing import Any

from jinja2 import Environment, StrictUndefined

from ..application.repositories.base_render import ITemplateRenderer


class JinjaRenderer(ITemplateRenderer):
    def __init__(self):
        self.env = Environment(undefined=StrictUndefined)

    async def render(self, template_md: str, payload: dict[str, Any]) -> str:
        """Toma el molde (Markdown con llaves) y el diccionario de datos. Retorna el Markdown final inyectado."""
        template = self.env.from_string(template_md)
        template = template.render(**payload)
        return template
