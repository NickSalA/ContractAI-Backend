"""Factory module for creating and configuring the FastAPI application."""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.contractai_backend.shared.config import settings

from src.contractai_backend.modules.documents.api.routers import router as documents_router
from src.contractai_backend.modules.users.api.routers import users_router, auth_router

def create() -> FastAPI:
    """Creates and configures the FastAPI application."""

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        """Lifespan context manager for startup and shutdown events."""
        # Aquí puedes agregar cualquier lógica de inicialización que necesites
        yield
        # Aquí puedes agregar cualquier lógica de limpieza que necesites

    app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

    app.include_router(documents_router, prefix="/documents", tags=["documents"])
    app.include_router(auth_router, prefix="/login", tags=["Autenticación"])
    app.include_router(users_router, prefix="/user", tags=["Usuarios"])
