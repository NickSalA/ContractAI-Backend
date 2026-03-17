"""Use case for deleting a document."""

from src.contractai_backend.modules.documents.application.interfaces.document_repo import IDocumentRepository


class DeleteDocumentUseCase:
    """Use case for deleting a document."""
    def __init__(
        self,
        document_repo: IDocumentRepository
        ):
        self._doc_repo = document_repo

    async def execute(self, document_id: str) -> None:
        """Deletes a document by its ID."""
        await self._doc_repo.delete(document_id)
