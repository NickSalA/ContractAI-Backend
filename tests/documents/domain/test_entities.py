"""Tests unitarios para las entidades del dominio de documentos."""

from datetime import date

import pytest

from contractai_backend.modules.documents.domain.entities import DocumentTable
from contractai_backend.modules.documents.domain.value_objs import DocumentState, DocumentType


def _valid_doc(**overrides) -> dict:
    base = {
        "name": "Contrato Ejemplo",
        "client": "Acme Corp",
        "type": DocumentType.LICENSES,
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "value": 5000.0,
        "currency": "PEN",
        "licenses": 10,
    }
    base.update(overrides)
    return base


class TestDocumentTableValidation:
    def test_creates_valid_document(self):
        doc = DocumentTable.model_validate(_valid_doc())
        assert doc.name == "Contrato Ejemplo"
        assert doc.state == DocumentState.ACTIVE

    def test_currency_must_be_uppercased(self):
        with pytest.raises(ValueError, match="Currency code must be uppercase"):
            DocumentTable.model_validate(_valid_doc(currency="pen"))

    def test_end_date_before_start_date_raises(self):
        with pytest.raises(ValueError, match="End date cannot be earlier than start date"):
            DocumentTable.model_validate(_valid_doc(start_date=date(2024, 6, 1), end_date=date(2024, 1, 1)))

    def test_negative_value_raises(self):
        with pytest.raises(ValueError, match="Value must be a positive number"):
            DocumentTable.model_validate(_valid_doc(value=-100.0))

    def test_zero_value_is_valid(self):
        doc = DocumentTable.model_validate(_valid_doc(value=0.0))
        assert doc.value == 0.0

    def test_negative_licenses_raises(self):
        with pytest.raises(ValueError, match="Licenses must be a non-negative integer"):
            DocumentTable.model_validate(_valid_doc(licenses=-1))

    def test_zero_licenses_is_valid(self):
        doc = DocumentTable.model_validate(_valid_doc(licenses=0))
        assert doc.licenses == 0

    def test_currency_wrong_length_raises(self):
        with pytest.raises(ValueError, match="Currency code must be a 3-letter string"):
            DocumentTable.model_validate(_valid_doc(currency="US"))

    def test_currency_too_long_raises(self):
        with pytest.raises(ValueError, match="Currency code must be a 3-letter string"):
            DocumentTable.model_validate(_valid_doc(currency="USDX"))

    def test_same_start_and_end_date_is_valid(self):
        doc = DocumentTable.model_validate(_valid_doc(start_date=date(2024, 6, 1), end_date=date(2024, 6, 1)))
        assert doc.start_date == doc.end_date

    def test_default_state_is_active(self):
        doc = DocumentTable.model_validate(_valid_doc())
        assert doc.state == DocumentState.ACTIVE

    def test_file_path_defaults_to_none(self):
        doc = DocumentTable.model_validate(_valid_doc())
        assert doc.file_path is None
        assert doc.file_name is None

    def test_all_document_types_are_accepted(self):
        for doc_type in DocumentType:
            doc = DocumentTable.model_validate(_valid_doc(type=doc_type))
            assert doc.type == doc_type

    def test_all_document_states_can_be_set(self):
        for state in DocumentState:
            doc = DocumentTable.model_validate(_valid_doc(state=state))
            assert doc.state == state
