"""Servicio de alertas diarias por correo electrónico para contratos por vencer."""

import html
from datetime import date, timedelta

from loguru import logger
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.core.exceptions.base import InternalServerError, ServiceUnavailableError
from contractai_backend.modules.documents.domain import DocumentTable
from contractai_backend.modules.documents.domain.value_objs import DocumentState
from contractai_backend.modules.notifications.infrastructure.gmail_service import GmailService
from contractai_backend.modules.users.domain.entities import UserTable
from contractai_backend.modules.users.domain.value_objs import UserRole

# (días_restantes, etiqueta, color_badge, color_bg, color_borde, color_texto, color_subtexto, emoji)
_THRESHOLD_STYLES: list[tuple[int, str, str, str, str, str, str, str]] = [
    (3, "VENCE EN 3 DÍAS — CRÍTICO", "#EF4444", "#FEF2F2", "#FECACA", "#991B1B", "#B91C1C", "🚨"),
    (7, "VENCE EN 7 DÍAS — ADVERTENCIA", "#F97316", "#FFF7ED", "#FED7AA", "#9A3412", "#C2410C", "⚠️"),
    (15, "VENCE EN 15 DÍAS — AVISO", "#3B82F6", "#EFF6FF", "#BFDBFE", "#1E40AF", "#1D4ED8", "📋"),
]


class EmailAlertService:
    def __init__(self, session: AsyncSession, gmail_service: GmailService):
        self.session = session
        self.gmail_service = gmail_service

    async def send_daily_alerts(self, organization_id: int) -> int:
        """Envía un correo consolidado a cada worker con los contratos por vencer.

        - Un solo correo por usuario con todas las alertas del día.
        - Si no hay contratos por vencer, no envía ningún correo.
        - Si el envío a un usuario falla, continúa con los demás.
        - Retorna el número de correos enviados exitosamente.
        """
        today = date.today()

        # Recopilar contratos por umbral
        contracts_by_threshold: dict[int, list[DocumentTable]] = {}
        for days, *_ in _THRESHOLD_STYLES:
            target_date = today + timedelta(days=days)
            docs = await self._get_expiring_documents(organization_id, target_date)
            if docs:
                contracts_by_threshold[days] = docs

        if not contracts_by_threshold:
            logger.info("Sin contratos por vencer para org {}. No se envían correos.", organization_id)
            return 0

        workers = await self._get_worker_users(organization_id)
        if not workers:
            logger.info("Sin usuarios WORKER activos para org {}.", organization_id)
            return 0

        total_contracts = sum(len(docs) for docs in contracts_by_threshold.values())
        sections_html = self._build_sections(contracts_by_threshold)
        date_str = today.strftime("%d/%m/%Y")
        subject = f"ContractAI — {total_contracts} contrato(s) por vencer hoy"

        sent = 0
        for worker in workers:
            name = html.escape(worker.full_name or worker.email)
            body = self._build_email_html(
                name=name,
                total=total_contracts,
                sections=sections_html,
                date_str=date_str,
            )
            try:
                await self.gmail_service.send_email(
                    to=worker.email,
                    subject=subject,
                    html_body=body,
                )
                sent += 1
            except Exception as e:
                logger.error("No se pudo enviar correo a {}: {}", worker.email, e)

        return sent

    # ─── Queries ────────────────────────────────────────────────────────────────

    async def _get_expiring_documents(self, organization_id: int, target_date: date) -> list[DocumentTable]:
        try:
            query = select(DocumentTable).where(
                DocumentTable.organization_id == organization_id,
                DocumentTable.end_date == target_date,
                DocumentTable.state == DocumentState.ACTIVE,
            )
            result = await self.session.exec(query)
            return list(result.all())
        except OperationalError as e:
            raise ServiceUnavailableError("La base de datos no está disponible") from e
        except SQLAlchemyError as e:
            raise InternalServerError("Error al consultar contratos") from e

    async def _get_worker_users(self, organization_id: int) -> list[UserTable]:
        try:
            query = select(UserTable).where(
                UserTable.organization_id == organization_id,
                UserTable.role == UserRole.WORKER,
                UserTable.is_active == True,  # noqa: E712
            )
            result = await self.session.exec(query)
            return list(result.all())
        except OperationalError as e:
            raise ServiceUnavailableError("La base de datos no está disponible") from e
        except SQLAlchemyError as e:
            raise InternalServerError("Error al consultar usuarios") from e

    # ─── Construcción del HTML ───────────────────────────────────────────────────

    def _build_sections(self, contracts_by_threshold: dict[int, list[DocumentTable]]) -> str:
        sections = []
        for days, label, badge_color, bg_color, border_color, text_color, subtext_color, emoji in _THRESHOLD_STYLES:
            docs = contracts_by_threshold.get(days)
            if not docs:
                continue

            items_html = ""
            for i, doc in enumerate(docs):
                is_last = i == len(docs) - 1
                border_bottom = "" if is_last else f"border-bottom:1px solid {border_color};"
                items_html += f"""
                <div style="padding:14px 18px;background:{bg_color};{border_bottom}">
                  <p style="margin:0 0 3px;color:{text_color};font-size:14px;font-weight:600;">{html.escape(doc.name)}</p>
                  <p style="margin:0;color:{subtext_color};font-size:13px;">
                    Cliente: {html.escape(doc.client)}&nbsp;&nbsp;·&nbsp;&nbsp;Vence: {doc.end_date.strftime("%d/%m/%Y")}
                  </p>
                </div>"""

            sections.append(f"""
            <div style="margin-bottom:20px;">
              <div style="margin-bottom:10px;">
                <span style="display:inline-block;background:{badge_color};color:#ffffff;font-size:11px;font-weight:700;
                             letter-spacing:0.4px;padding:4px 14px;border-radius:20px;">
                  {emoji} {label}
                </span>
              </div>
              <div style="border-radius:8px;overflow:hidden;border:1px solid {border_color};">
                {items_html}
              </div>
            </div>""")

        return "\n".join(sections)

    def _build_email_html(self, name: str, total: int, sections: str, date_str: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ContractAI — Alertas de contratos</title>
</head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#F1F5F9;padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;">

          <!-- HEADER -->
          <tr>
            <td style="background:linear-gradient(135deg,#1E3A8A 0%,#3B82F6 100%);
                       padding:36px 40px;border-radius:12px 12px 0 0;text-align:center;">
              <div style="display:inline-block;background:rgba(255,255,255,0.15);
                          border-radius:8px;padding:8px 24px;margin-bottom:14px;">
                <span style="color:#ffffff;font-size:22px;font-weight:700;letter-spacing:1px;">
                  ContractAI
                </span>
              </div>
              <p style="margin:0;color:#BFDBFE;font-size:12px;letter-spacing:0.8px;text-transform:uppercase;">
                Resumen de alertas &nbsp;·&nbsp; {date_str}
              </p>
            </td>
          </tr>

          <!-- BODY -->
          <tr>
            <td style="background:#ffffff;padding:36px 40px;">

              <p style="margin:0 0 6px;color:#111827;font-size:17px;font-weight:600;">
                Hola, {name} 👋
              </p>
              <p style="margin:0 0 28px;color:#6B7280;font-size:14px;line-height:1.7;">
                Tienes <strong style="color:#1E3A8A;">{total} contrato(s)</strong>
                que requieren tu atención hoy.
              </p>

              {sections}

              <div style="margin-top:24px;padding:16px 20px;background:#F0F9FF;
                          border-radius:8px;border-left:4px solid #3B82F6;">
                <p style="margin:0;color:#1E40AF;font-size:13px;line-height:1.7;">
                  💡 <strong>Tip:</strong> Accede a ContractAI para revisar los detalles,
                  renovar contratos o gestionar las alertas.
                </p>
              </div>

            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="background:#F8FAFC;padding:24px 40px;
                       border-radius:0 0 12px 12px;border-top:1px solid #E2E8F0;">
              <p style="margin:0 0 4px;color:#9CA3AF;font-size:12px;text-align:center;">
                Enviado automáticamente por
                <strong style="color:#6B7280;">ContractAI</strong>
              </p>
              <p style="margin:0;color:#B0BAC5;font-size:11px;text-align:center;">
                Por favor no respondas a este mensaje.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
