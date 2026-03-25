"""Value objects para la gestión de usuarios."""

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    WORKER = "worker"
