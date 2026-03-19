"""Value objects for the Documents domain."""
from enum import StrEnum


class DocumentType(StrEnum):
    """Enum-like class to represent document types."""
    LICENSES = "LICENCIAS"
    SERVICES = "SERVICIOS"
    SUPPORT = "SOPORTE"

class DocumentState(StrEnum):
    """Enum-like class to represent document states."""
    ACTIVE = "ACTIVO"
    EXPIRED = "EXPIRADO"
    PENDING = "POR_VENCER"
