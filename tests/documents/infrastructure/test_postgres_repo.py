"""Tests unitarios para SQLModelDocumentRepository con sesión mockeada."""

from collections.abc import Sequence
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from contractai_backend.modules.documents.domain.entities import DocumentTable
from contractai_backend.modules.documents.domain.exceptions import DocumentDatabaseError, DocumentDatabaseUnavailableError
from contractai_backend.modules.documents.domain.value_objs import DocumentState, DocumentType
from contractai_backend.modules.documents.infrastructure.postgres_repo import SQLModelDocumentRepository


def _make_doc(id: int = 1) -> DocumentTable:
    return DocumentTable(
        id=id,
        name="Contrato Test",
        client="Cliente Test",
        type=DocumentType.LICENSES,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        value=1000.0,
        currency="PEN",
        licenses=5,
        state=DocumentState.ACTIVE,
    )


def _make_repo() -> tuple[SQLModelDocumentRepository, AsyncMock]:
    session = AsyncMock()
    repo = SQLModelDocumentRepository(session=session)
    return repo, session


class TestGetByClientName:
    @pytest.mark.asyncio
    async def test_returns_documents_for_client(self):
        repo, session = _make_repo()
        docs = [_make_doc(1), _make_doc(2)]

        result_mock = MagicMock()
        result_mock.all.return_value = docs
        session.exec.return_value = result_mock

        result = await repo.get_by_client_name("Cliente Test")

        assert result == docs
        session.exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_match(self):
        repo, session = _make_repo()
        result_mock = MagicMock()
        result_mock.all.return_value = []
        session.exec.return_value = result_mock

        result = await repo.get_by_client_name("Desconocido")

        assert result == []

    @pytest.mark.asyncio
    async def test_operational_error_raises_unavailable(self):
        repo, session = _make_repo()
        session.exec.side_effect = OperationalError("conn", {}, Exception())

        with pytest.raises(DocumentDatabaseUnavailableError):
            await repo.get_by_client_name("Cliente Test")

    @pytest.mark.asyncio
    async def test_sqlalchemy_error_raises_database_error(self):
        repo, session = _make_repo()
        session.exec.side_effect = SQLAlchemyError("query error")

        with pytest.raises(DocumentDatabaseError):
            await repo.get_by_client_name("Cliente Test")


class TestGetActiveDocuments:
    @pytest.mark.asyncio
    async def test_returns_active_documents(self):
        repo, session = _make_repo()
        docs = [_make_doc(1)]
        result_mock = MagicMock()
        result_mock.all.return_value = docs
        session.exec.return_value = result_mock

        result = await repo.get_active_documents()

        assert result == docs

    @pytest.mark.asyncio
    async def test_operational_error_raises_unavailable(self):
        repo, session = _make_repo()
        session.exec.side_effect = OperationalError("conn", {}, Exception())

        with pytest.raises(DocumentDatabaseUnavailableError):
            await repo.get_active_documents()

    @pytest.mark.asyncio
    async def test_sqlalchemy_error_raises_database_error(self):
        repo, session = _make_repo()
        session.exec.side_effect = SQLAlchemyError("query error")

        with pytest.raises(DocumentDatabaseError):
            await repo.get_active_documents()
