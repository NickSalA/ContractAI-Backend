"""Provides structured contract queries for analytics-style use cases."""

from datetime import date
from typing import Any

from ...domain import CurrencyType, DocumentState, DocumentTable, DocumentType
from ..repositories import DocumentQueryRepository

VALID_DATE_MODES = {"overlap", "start_date", "end_date"}
DEFAULT_LIST_LIMIT = 20
MAX_LIST_LIMIT = 50


class ContractQueryService:
    """Executes structured contract queries backed by the relational store."""

    def __init__(self, sql_repo: DocumentQueryRepository):
        self.sql_repo = sql_repo

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @staticmethod
    def _normalize_currency(currency: str | None) -> CurrencyType | None:
        if currency is None:
            return None

        normalized = currency.strip().upper()
        return CurrencyType(normalized)

    @staticmethod
    def _normalize_state(state: str | None) -> DocumentState | None:
        if state is None:
            return None

        normalized = state.strip().upper()
        return DocumentState(normalized)

    @staticmethod
    def _normalize_document_type(document_type: str | None) -> DocumentType | None:
        if document_type is None:
            return None

        normalized = document_type.strip().upper()
        return DocumentType(normalized)

    @staticmethod
    def _normalize_date_mode(date_mode: str | None) -> str:
        normalized = (date_mode or "overlap").strip().lower()
        if normalized not in VALID_DATE_MODES:
            raise ValueError("date_mode invalido")
        return normalized

    @staticmethod
    def _parse_date(value: str | date | None) -> date | None:
        if value is None or value == "":
            return None
        if isinstance(value, date):
            return value
        return date.fromisoformat(value.strip())

    @staticmethod
    def _clamp_limit(limit: int | None) -> int:
        if limit is None:
            return DEFAULT_LIST_LIMIT
        return max(1, min(limit, MAX_LIST_LIMIT))

    @staticmethod
    def _serialize_contract(document: DocumentTable) -> dict[str, Any]:
        form_data = document.form_data if isinstance(document.form_data, dict) else {}

        return {
            "id": document.id,
            "name": document.name,
            "client": document.client,
            "type": document.type.value if hasattr(document.type, "value") else str(document.type),
            "state": document.state.value if hasattr(document.state, "value") else str(document.state),
            "start_date": document.start_date.isoformat(),
            "end_date": document.end_date.isoformat(),
            "value": form_data.get("value"),
            "currency": form_data.get("currency"),
            "file_name": document.file_name,
        }

    async def run_query(  # noqa: PLR0913
        self,
        organization_id: int,
        operation: str,
        client: str | None = None,
        contract_name: str | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        currency: str | None = None,
        state: str | None = None,
        document_type: str | None = None,
        period_start: str | date | None = None,
        period_end: str | date | None = None,
        date_mode: str | None = "overlap",
        limit: int | None = None,
    ) -> dict[str, Any]:
        normalized_operation = operation.strip().lower()
        if normalized_operation not in {"count", "list"}:
            return {
                "status": "invalid_request",
                "message": "La operacion debe ser 'count' o 'list'.",
            }

        if (min_value is not None or max_value is not None) and not currency:
            return {
                "status": "needs_clarification",
                "message": "Indique la moneda del monto a evaluar, por ejemplo USD, PEN o EUR.",
            }

        try:
            normalized_currency = self._normalize_currency(currency=currency)
            normalized_state = self._normalize_state(state=state)
            normalized_document_type = self._normalize_document_type(document_type=document_type)
            normalized_date_mode = self._normalize_date_mode(date_mode=date_mode)
            parsed_period_start = self._parse_date(period_start)
            parsed_period_end = self._parse_date(period_end)
        except ValueError as exc:
            return {
                "status": "invalid_request",
                "message": f"No se pudo interpretar uno de los filtros proporcionados: {exc}",
            }

        if parsed_period_start and parsed_period_end and parsed_period_start > parsed_period_end:
            return {
                "status": "invalid_request",
                "message": "La fecha inicial no puede ser posterior a la fecha final.",
            }

        normalized_client = self._normalize_optional_text(client)
        normalized_contract_name = self._normalize_optional_text(contract_name)
        resolved_limit = self._clamp_limit(limit)

        total_contracts = await self.sql_repo.count_contracts(organization_id=organization_id)
        if total_contracts == 0:
            return {
                "status": "no_data",
                "message": "No hay contratos cargados para la organizacion actual.",
            }

        query_kwargs = {
            "organization_id": organization_id,
            "client": normalized_client,
            "contract_name": normalized_contract_name,
            "min_value": min_value,
            "max_value": max_value,
            "currency": normalized_currency,
            "state": normalized_state,
            "document_type": normalized_document_type,
            "period_start": parsed_period_start,
            "period_end": parsed_period_end,
            "date_mode": normalized_date_mode,
        }

        filtered_count = await self.sql_repo.count_contracts(**query_kwargs)

        response: dict[str, Any] = {
            "status": "success",
            "operation": normalized_operation,
            "count": filtered_count,
            "total_contracts_available": total_contracts,
            "filters_applied": {
                "client": normalized_client,
                "contract_name": normalized_contract_name,
                "min_value": min_value,
                "max_value": max_value,
                "currency": normalized_currency,
                "state": normalized_state,
                "document_type": normalized_document_type,
                "period_start": parsed_period_start.isoformat() if parsed_period_start else None,
                "period_end": parsed_period_end.isoformat() if parsed_period_end else None,
                "date_mode": normalized_date_mode,
            },
        }

        if normalized_operation == "count":
            return response

        documents = await self.sql_repo.search_contracts(**query_kwargs, limit=resolved_limit)
        response["items"] = [self._serialize_contract(document=document) for document in documents]
        response["returned_items"] = len(response["items"])
        response["limit"] = resolved_limit
        return response
