"""Module containing use cases for retrieving documents."""

from typing import List, Optional

from contractai_backend.modules.documents.application.interfaces.document_repo import IDocumentRepository
from contractai_backend.modules.documents.domain import Document


class GetDocumentUseCase:
    """Use case for retrieving a document by its ID."""
    def __init__(
        self,
        doc_repo: IDocumentRepository,
    ):
        self._doc_repo = doc_repo

    def execute(self, document_id: int) -> Optional[Document]:
        """Retrieves a document by its ID."""
        return self._doc_repo.get(document_id)

class ListDocumentsByClientUseCase:
    """Use case for listing all documents for a given client."""
    def __init__(
        self,
        doc_repo: IDocumentRepository,
    ):
        self._doc_repo = doc_repo

    def execute(self, client_name: str) -> List[Document]:
        """Lists all documents for a given client."""
        return self._doc_repo.get_by_client_name(client_name)

class ListActiveDocumentsUseCase:
    """Use case for listing all active documents."""
    def __init__(
        self,
        doc_repo: IDocumentRepository,
    ):
        self._doc_repo = doc_repo

    def execute(self) -> List[Document]:
        """Lists all active documents."""
        return self._doc_repo.get_active_documents()

class ListDocumentUseCase:
    """Use case for listing all documents."""
    def __init__(
        self,
        doc_repo: IDocumentRepository,
    ):
        self._doc_repo = doc_repo

    def execute(self) -> List[Document]:
        """Lists all documents."""
        return self._doc_repo.list_all()
