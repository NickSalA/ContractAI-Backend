"""Value objects for the Documents domain."""
from enum import Enum


class DocumentType(str, Enum):
    """Enum-like class to represent document types."""
    LICENSES = "LICENCIAS"
    SERVICES = "SERVICIOS"
    SUPPORT = "SOPORTE"

class DocumentState(str, Enum):
    """Enum-like class to represent document states."""
    ACTIVE = "ACTIVO"
    EXPIRED = "EXPIRADO"
    PENDING = "POR_VENCER"
