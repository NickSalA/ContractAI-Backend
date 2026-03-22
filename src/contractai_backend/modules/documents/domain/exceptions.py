"""Excepciones personalizadas para el módulo de documentos."""

from ....core.exceptions.base import BadGatewayError, InternalServerError, NotFoundError, ValidationError


class DocumentNotFoundError(NotFoundError):
    """Se lanza cuando un documento no existe en la base de datos."""
    def __init__(self, document_id: int):
        super().__init__(message=f"El documento con ID {document_id} no fue encontrado.")


class DocumentFileMissingError(NotFoundError):
    """Se lanza cuando se solicita un archivo físico de un documento que no lo tiene."""
    def __init__(self, document_id: int):
        super().__init__(message=f"El documento con ID {document_id} no tiene un archivo asociado.")


class InvalidDocumentFileError(ValidationError):
    """Se lanza cuando el archivo subido no tiene los metadatos requeridos (nombre o tipo)."""
    def __init__(self, message: str = "El nombre del archivo y el tipo de contenido son obligatorios."):
        super().__init__(message)


class DocumentExtractionError(BadGatewayError):
    """Se lanza cuando LlamaParse o el extractor fallan al procesar el archivo."""
    def __init__(self, message: str = "Fallo al extraer los datos del documento."):
        super().__init__(message)


class DocumentTransactionError(InternalServerError):
    """Se lanza cuando falla la orquestación (Saga) entre SQL, Storage y VectorDB."""
    def __init__(self, operation: str, details: str):
        super().__init__(message=f"Falló la transacción de {operation} del documento: {details}")
