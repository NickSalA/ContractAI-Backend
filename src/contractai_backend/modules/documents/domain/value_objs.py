"""Value objects for the Documents domain."""

from enum import StrEnum


class DocumentType(StrEnum):
    """Tipos de documento permitidos por la base de datos."""

    SERVICES = "SERVICES"
    LICENSES = "LICENSES"
    SUPPORT = "SUPPORT"


class DocumentState(StrEnum):
    """Estados de documento permitidos por la base de datos."""

    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"


class CurrencyType(StrEnum):
    """Monedas permitidas para los servicios asociados a un documento."""

    PEN = "PEN"
    USD = "USD"
    EUR = "EUR"
