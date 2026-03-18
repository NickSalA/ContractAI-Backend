"""Value objects for the Documents domain."""
from dataclasses import dataclass
from datetime import date
from enum import Enum


@dataclass(frozen=True)
class DocumentPeriod:
    """Value object that represents the period of a document."""
    start: date
    end: date

    def __post_init__(self):
        """Validates that the start date is before the end date."""
        if self.start > self.end:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin.")

@dataclass(frozen=True)
class Money:
    """Value object that represents a monetary value."""
    amount: float
    currency: str = "PEN"

    def __post_init__(self):
        """Validates that the amount is non-negative."""
        if self.amount < 0:
            raise ValueError("El valor del contrato no puede ser negativo.")

class DocumentType(str, Enum):
    """Enum-like class to represent document types."""
    LICENSES = "LICENCIAS"
    SERVICES = "SERVICIOS"
    SOPORTE = "SOPORTE"

class DocumentState(str, Enum):
    """Enum-like class to represent document states."""
    ACTIVE = "ACTIVO"
    EXPIRED = "EXPIRADO"
    PENDING = "POR_VENCER"
