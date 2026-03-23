"""Tests unitarios para LlamaParseExtractor mockeando LlamaParse y el filesystem."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from contractai_backend.modules.documents.domain.exceptions import DocumentExtractionError
from contractai_backend.modules.documents.infrastructure.llama_parser import LlamaParseExtractor


def _make_extractor() -> LlamaParseExtractor:
    with patch("contractai_backend.modules.documents.infrastructure.llama_parser.settings") as mock_settings:
        mock_settings.LLAMA_PARSE_API_KEY = "fake-key"
        with patch("contractai_backend.modules.documents.infrastructure.llama_parser.LlamaParse"):
            extractor = LlamaParseExtractor()
    return extractor


class TestLlamaParseExtractor:
    @pytest.mark.asyncio
    async def test_extract_returns_documents_with_filename_metadata(self):
        extractor = _make_extractor()

        doc1 = MagicMock()
        doc1.metadata = {}
        extractor.parser.aload_data = AsyncMock(return_value=[doc1])

        result = await extractor.extract(b"pdf content", "contrato.pdf")

        assert len(result) == 1
        assert result[0].metadata["filename"] == "contrato.pdf"

    @pytest.mark.asyncio
    async def test_extract_returns_multiple_documents(self):
        extractor = _make_extractor()

        docs = [MagicMock(metadata={}), MagicMock(metadata={})]
        extractor.parser.aload_data = AsyncMock(return_value=docs)

        result = await extractor.extract(b"pdf content", "contrato.pdf")

        assert len(result) == 2
        for doc in result:
            assert doc.metadata["filename"] == "contrato.pdf"

    @pytest.mark.asyncio
    async def test_extract_parser_error_raises_extraction_error(self):
        extractor = _make_extractor()
        extractor.parser.aload_data = AsyncMock(side_effect=Exception("API error"))

        with pytest.raises(DocumentExtractionError, match="contrato.pdf"):
            await extractor.extract(b"pdf content", "contrato.pdf")

    @pytest.mark.asyncio
    async def test_extract_cleans_up_temp_file_on_success(self):
        extractor = _make_extractor()
        extractor.parser.aload_data = AsyncMock(return_value=[MagicMock(metadata={})])

        with patch("contractai_backend.modules.documents.infrastructure.llama_parser.Path") as mock_path_cls:
            mock_path = MagicMock()
            mock_path.suffix.lower.return_value = ".pdf"
            mock_path.exists.return_value = True
            mock_path_cls.return_value = mock_path

            with patch("contractai_backend.modules.documents.infrastructure.llama_parser.tempfile.NamedTemporaryFile") as mock_tmp:
                mock_file = MagicMock()
                mock_file.__enter__ = MagicMock(return_value=mock_file)
                mock_file.__exit__ = MagicMock(return_value=False)
                mock_file.name = "/tmp/test.pdf"
                mock_tmp.return_value = mock_file

                await extractor.extract(b"content", "contrato.pdf")

    @pytest.mark.asyncio
    async def test_extract_cleans_up_temp_file_on_error(self):
        extractor = _make_extractor()
        extractor.parser.aload_data = AsyncMock(side_effect=Exception("fail"))

        with patch("contractai_backend.modules.documents.infrastructure.llama_parser.Path") as mock_path_cls:
            mock_path = MagicMock()
            mock_path.suffix.lower.return_value = ".pdf"
            mock_path.exists.return_value = True
            mock_path_cls.return_value = mock_path

            with patch("contractai_backend.modules.documents.infrastructure.llama_parser.tempfile.NamedTemporaryFile") as mock_tmp:
                mock_file = MagicMock()
                mock_file.__enter__ = MagicMock(return_value=mock_file)
                mock_file.__exit__ = MagicMock(return_value=False)
                mock_file.name = "/tmp/test.pdf"
                mock_tmp.return_value = mock_file

                with pytest.raises(DocumentExtractionError):
                    await extractor.extract(b"content", "contrato.pdf")
