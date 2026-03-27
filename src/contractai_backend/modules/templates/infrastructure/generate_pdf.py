"""Módulo encargado de convertir el Markdown generado por el módulo de templates a PDF, utilizando WeasyPrint."""

from markdown2 import UnicodeWithAttrs, markdown
from weasyprint import CSS, HTML

from ..application.repositories.base_generate import IDocumentGenerator


class WeasyPrintGenerator(IDocumentGenerator):
    async def generate_pdf(self, markdown_content: str) -> bytes:
        """Convierte Markdown a PDF y retorna los bytes para que el módulo de documentos se encargue de guardarlos."""
        body_html: UnicodeWithAttrs = markdown(text=markdown_content, extras=["tables", "fenced_code-blocks"])
        style = """
        @page {
            size: A4;
            margin: 2.5cm;
            @bottom-right {
                content: "Página " counter(page) " de " counter(pages);
                font-size: 9pt;
            }
        }
        body {
            font-family: 'Times New Roman', serif;
            line-height: 1.5;
            text-align: justify;
            font-size: 11pt;
        }
        h1 { text-align: center; text-transform: uppercase; font-size: 14pt; }

        /* Contenedor de Firmas con Flexbox */
        .signature-container {
            display: flex;
            justify-content: space-between;
            margin-top: 80px;
            page-break-inside: avoid; /* Evita que la firma se parta entre páginas */
        }
        .sig-box {
            width: 40%;
            text-align: center;
        }
        .sig-line {
            border-top: 1px solid black;
            margin-bottom: 5px;
        }
        """

        full_html = f"""
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            {body_html}
        </body>
        </html>
        """
        pdf_bytes: bytes = HTML(string=full_html).write_pdf(stylesheets=[CSS(string=style)])

        return pdf_bytes
