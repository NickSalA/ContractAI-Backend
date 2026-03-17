"""Use case for uploading a document and saving its metadata to the repository."""

from src.contractai_backend.modules.documents.application.interfaces.document_repo import IDocumentRepository
from src.contractai_backend.modules.documents.domain import Document, DocumentState


class UploadDocumentUseCase:
    """Use case for uploading a document and saving its metadata to the repository."""
    def __init__(
        self,
        doc_repo: IDocumentRepository,
    ):
        self._doc_repo = doc_repo

    async def execute(self, file: bytes, doc_data: dict) -> Document:
        """Uploads a document and saves its metadata to the repository."""
        new_doc = Document(
            id=0,
            name=doc_data["name"],
            client=doc_data["client"],
            type=doc_data["type"],
            period=doc_data["period"],
            value=doc_data["value"],
            licenses=doc_data["licenses"],
            state=DocumentState.ACTIVE,
        )

        await self._doc_repo.save(new_doc)
        return new_doc
