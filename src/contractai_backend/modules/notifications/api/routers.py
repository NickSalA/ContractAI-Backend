"""Endpoints HTTP para el módulo de notificaciones."""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.core.exceptions.base import InternalServerError, ServiceUnavailableError
from contractai_backend.modules.documents.domain.entities import DocumentTable
from contractai_backend.modules.documents.domain.value_objs import DocumentState
from contractai_backend.modules.notifications.api.dependencies import get_email_alert_service
from contractai_backend.modules.notifications.api.schemas import NotificationResponse
from contractai_backend.modules.notifications.application.services.email_alert_service import EmailAlertService
from contractai_backend.modules.notifications.domain.value_objs import NotificationType
from contractai_backend.shared.api.dependencies.security import CurrentUserDep
from contractai_backend.shared.infrastructure.database import get_session

router = APIRouter()

EmailAlertServiceDep = Annotated[EmailAlertService, Depends(get_email_alert_service)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]

# (días_antes_de_vencer, tipo_de_alerta)
_THRESHOLDS: list[tuple[int, NotificationType]] = [
    (3, NotificationType.CRITICAL),
    (7, NotificationType.WARNING),
    (15, NotificationType.WARNING),
]


@router.get(path="/", response_model=list[NotificationResponse])
async def list_notifications(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[NotificationResponse]:
    """Consulta en tiempo real los contratos próximos a vencer.

    Retorna una notificación por cada contrato ACTIVO que vence en 3, 7 o 15 días.
    El estado leída/descartada es gestionado por el frontend via localStorage.
    """
    today = date.today()
    notifications: list[NotificationResponse] = []

    try:
        for days, notif_type in _THRESHOLDS:
            target_date = today + timedelta(days=days)
            result = await session.exec(
                select(DocumentTable).where(
                    DocumentTable.organization_id == current_user.organization_id,
                    DocumentTable.end_date == target_date,
                    DocumentTable.state == DocumentState.ACTIVE,
                )
            )
            for doc in result.all():
                notifications.append(
                    NotificationResponse(
                        id=f"contract-{doc.id}-{days}",
                        document_id=doc.id,
                        type=notif_type,
                        title=f"Contrato por vencer en {days} días: {doc.name}",
                        description=f"El contrato con {doc.client} vence el {doc.end_date.strftime('%d/%m/%Y')}.",
                        days_remaining=days,
                    )
                )
    except OperationalError as e:
        raise ServiceUnavailableError("La base de datos no está disponible") from e
    except SQLAlchemyError as e:
        raise InternalServerError("Error al consultar contratos") from e

    return notifications


@router.post(path="/send-email-alerts", status_code=200)
async def send_email_alerts(
    email_service: EmailAlertServiceDep,
    current_user: CurrentUserDep,
) -> dict:
    """Envía correos de alerta de vencimiento a todos los workers de la organización.

    Diseñado para ser invocado por un CRON externo a las 7:00 AM.
    Un solo correo por usuario, consolidando contratos que vencen en 3, 7 y 15 días.
    """
    sent = await email_service.send_daily_alerts(
        organization_id=current_user.organization_id,
    )
    return {"emails_sent": sent}
